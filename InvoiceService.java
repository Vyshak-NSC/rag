package com.microservices.verisaedataextract.service;

import com.microservices.verisaedataextract.dto.invoice.GetApiInvoiceResponse;
import com.microservices.verisaedataextract.dto.invoice.Inv;
import com.microservices.verisaedataextract.dto.invoice.Invoices;
import com.microservices.verisaedataextract.mapper.invoice.BatchMapper;
import com.microservices.verisaedataextract.mapper.invoice.*;
import com.microservices.verisaedataextract.models.invoice.*;
import com.microservices.verisaedataextract.parser.InvoiceXmlParser;
import com.microservices.verisaedataextract.repository.invoice.*;
import lombok.RequiredArgsConstructor;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.NoSuchFileException;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.Duration;

import lombok.extern.slf4j.Slf4j;
import org.springframework.web.reactive.function.client.WebClientRequestException;
import org.springframework.web.reactive.function.client.WebClientResponseException;
import reactor.util.retry.Retry;

@Slf4j
@Service
@RequiredArgsConstructor
public class InvoiceService {

    private final WebClient webClient;
    private final InvoiceXmlParser invoiceXmlParser;
    private final BatchMapper batchMapper;

    private final HeaderMapper headerMapper;
    private final DetailMapper detailMapper;
    private final DisbursementMapper disbursementMapper;
    private final DisbursementItemMapper disbursementItemtMapper;
    private final PartMapper partMapper;
    private final PartAdjMapper partAdjMapper;
    private final LaborAdjMapper laborAdjMapper;
    private final LaborChargeMapper laborChargeMapper;
    private final TravelChargeMapper travelChargeMapper;
    private final MiscChargeMapper miscChargeMapper;

    private final BatchRepository batchRepository;
    private final HeaderRowDataRepository headerRowDataRepository;
    private final DetailRowDataRepository detailRowDataRepository;
    private final DisbursementRowDataRepository disbursementRowDataRepository;
    private final DisbursementItemRepository disbursementItemRepository;
    private final PartRepository partRepository;
    private final PartAdjRepository partAdjRepository;
    private final LaborAdjRepository laborAdjRepository;
    private final LaborChargeRepository laborChargeRepository;
    private final TravelChargeReporistory travelChargeRepository;
    private final MiscChargeRepository miscChargeRepository;

    public String getInvoices(String token) throws IOException {

        Path path = Paths.get("extracts/api-invoice/request/request-api-invoice.xml");

        String xmlRequest;
        try {
            xmlRequest = Files.readString(path, StandardCharsets.UTF_8);
        } catch (NoSuchFileException e) {
            log.error("Request template not found at {}", path.toAbsolutePath());
            throw new IllegalStateException("Missing request template file: " + path, e);
        }

        String response;

        try {
            response = webClient
                    .post()
                    .uri("/getAPInvoices")
                    .contentType(MediaType.APPLICATION_XML)
                    .accept(MediaType.APPLICATION_XML)
                    .headers(headers -> headers.setBasicAuth(token))
                    .bodyValue(xmlRequest)
                    .retrieve()
                    .bodyToMono(String.class)

                    .timeout(Duration.ofSeconds(60))
                    .retryWhen(Retry.backoff(3, Duration.ofSeconds(2))
                            .filter(this::isRetryable)
                            .onRetryExhaustedThrow((spec, signal) -> signal.failure()))
                    .block();

        } catch (WebClientResponseException.Unauthorized | WebClientResponseException.Forbidden e) {
            log.error("Verisae rejected the token (HTTP {})", e.getStatusCode());
            throw new IllegalStateException("Authentication failed with Verisae — check the token", e);
        } catch (WebClientResponseException e) {
            log.error("Verisae returned HTTP {}: {}", e.getStatusCode(), e.getResponseBodyAsString());
            throw new IllegalStateException("Verisae API call failed with status " + e.getStatusCode(), e);
        } catch (WebClientRequestException e) {
            log.error("Could not reach Verisae: {}", e.getMessage());
            throw new IllegalStateException("Could not connect to Verisae (network/timeout)", e);
        }

        if (response == null || response.isBlank()) {
            log.error("Verisae returned an empty response body");
            throw new IllegalStateException("Verisae returned an empty response");
        }

        GetApiInvoiceResponse parsedResponse;
        try {
            parsedResponse = invoiceXmlParser.parse(response);
        } catch (Exception e) {
            log.error("Failed to parse Verisae XML response: {}", e.getMessage());
            archiveResponse(response, "response-api-invoice-FAILED.xml");
            throw new IllegalStateException("Failed to parse Verisae response as XML", e);
        }

//        extract from XML and save to db
        saveToDatabase(parsedResponse);


//        TEST - Manually from file
//        String response = Files.readString(Paths.get("extracts/api-invoice/response/response-api-invoice-fake.xml"), StandardCharsets.UTF_8);


        // Save response
        archiveResponse(response, "response-api-invoice.xml");

        return response;
    }

    private boolean isRetryable(Throwable throwable) {
        if (throwable instanceof WebClientRequestException) {
            return true; // connection refused, DNS failure, read timeout, etc.
        }
        if (throwable instanceof WebClientResponseException e) {
            return e.getStatusCode().is5xxServerError()
                    || e.getStatusCode().value() == 429; // rate limited
        }
        return false;
    }

    private void archiveResponse(String response, String filename) {
        try {
            Path responsePath = Paths.get("extracts/api-invoice/response/" + filename);
            Files.createDirectories(responsePath.getParent());
            Files.writeString(responsePath, response, StandardCharsets.UTF_8);
        } catch (IOException e) {
            log.error("Failed to write response archive to {}: {}", filename, e.getMessage());
        }
    }

    public void saveToDatabase(GetApiInvoiceResponse parsedResponse){
        Invoices invoices = parsedResponse.getClient().getInvoices();

        if(invoices == null || invoices.getInvoiceList() == null) return;

        // Add batch entry if invoice list nto empty
        Batch batch = batchRepository.save(batchMapper.mapBatch(invoices, parsedResponse.getDateProcessed()));

        // For every invoice add to Header, Detail, Disbursement entry with batch_no
        for (Inv inv : invoices.getInvoiceList()){
            String workOrderNumber = inv.getWorkOrderNumber();
            if(headerRowDataRepository.existsByWorkOrderNumber(workOrderNumber)){
                log.warn("Skipping duplicate invoice with work order number: {}", workOrderNumber);
                continue;
            }
            try {
                HeaderRowData header = headerRowDataRepository.save(
                        headerMapper.toHeader(inv, batch)
                );
                if (inv.getDisbursements() != null) {
                    DisbursementRowData disbursement = disbursementRowDataRepository.save(
                            disbursementMapper.toDisbursements(inv, header)
                    );

                    var dis = inv.getDisbursements();

                    if (dis.getDisbursement() != null) {
                        disbursementItemRepository.saveAll(
                                disbursementItemtMapper.toDisbursementItem(inv.getDisbursements().getDisbursement(), disbursement)
                        );
                    }
                }

                if (inv.getDetail() != null) {
                    DetailRowData details = detailRowDataRepository.save(
                            detailMapper.toDetail(inv, header)
                    );

                    // map details
                    var det = inv.getDetail();

                    //save part children if it exists
                    if (det.getParts() != null) {
                        partRepository.saveAll(
                                partMapper.toPart(det.getParts().getPart(), details));

                        partAdjRepository.saveAll(
                                partAdjMapper.toPartAdj(det.getParts().getPartAdj(), details));
                    }

                    //save labor children if it exists
                    if (det.getLabor() != null) {
                        laborChargeRepository.saveAll(
                                laborChargeMapper.toLaborCharge(det.getLabor().getLaborCharge(), details));

                        laborAdjRepository.saveAll(
                                laborAdjMapper.toLaborAdj(det.getLabor().getLaborAdj(), details));
                    }

                    //save misc children if it exists
                    if (det.getMisc() != null) {
                        miscChargeRepository.saveAll(
                                miscChargeMapper.toMiscCharge(det.getMisc().getMiscCharge(), details));
                    }

                    //save travel children if it exists
                    if (det.getTravel() != null) {
                        travelChargeRepository.saveAll(
                                travelChargeMapper.toTravelCharge(det.getTravel().getTravelCharge(), details));
                    }
                }
            }catch (Exception e){
                log.error("Failed to save invoice {}:{}",workOrderNumber, e.getMessage());
            }
        }
    }
}

