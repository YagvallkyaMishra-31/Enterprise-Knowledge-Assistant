package com.knowledgeassistant.backend.controller;

import com.knowledgeassistant.backend.config.CustomUserDetails;
import com.knowledgeassistant.backend.dto.DocumentResponse;
import com.knowledgeassistant.backend.service.DocumentService;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;
import java.util.UUID;

/**
 * REST controller for document upload and management.
 *
 * <p>All endpoints require a valid JWT. The authenticated user's ID is
 * extracted from the SecurityContext to enforce per-user isolation (USP #5).</p>
 */
@RestController
@RequestMapping("/api/documents")
public class DocumentController {

    private final DocumentService documentService;

    public DocumentController(DocumentService documentService) {
        this.documentService = documentService;
    }

    /** Uploads a document file and creates a PENDING database record. */
    @PostMapping(consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<DocumentResponse> uploadDocument(
            @RequestParam("file") MultipartFile file,
            @AuthenticationPrincipal CustomUserDetails principal) {
        DocumentResponse response = documentService.uploadDocument(file, principal.getId());
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    /** Lists all documents owned by the authenticated user, newest first. */
    @GetMapping
    public ResponseEntity<List<DocumentResponse>> listDocuments(
            @AuthenticationPrincipal CustomUserDetails principal) {
        return ResponseEntity.ok(documentService.listDocuments(principal.getId()));
    }

    /** Returns a single document if owned by the requesting user; 404 otherwise. */
    @GetMapping("/{id}")
    public ResponseEntity<DocumentResponse> getDocument(
            @PathVariable UUID id,
            @AuthenticationPrincipal CustomUserDetails principal) {
        return ResponseEntity.ok(documentService.getDocument(id, principal.getId()));
    }

    /** Deletes a document (DB row + physical file) if owned by the requesting user. */
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteDocument(
            @PathVariable UUID id,
            @AuthenticationPrincipal CustomUserDetails principal) {
        documentService.deleteDocument(id, principal.getId());
        return ResponseEntity.noContent().build();
    }
}
