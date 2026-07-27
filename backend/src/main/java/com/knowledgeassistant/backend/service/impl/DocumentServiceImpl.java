package com.knowledgeassistant.backend.service.impl;

import com.knowledgeassistant.backend.dto.DocumentResponse;
import com.knowledgeassistant.backend.entity.Document;
import com.knowledgeassistant.backend.entity.User;
import com.knowledgeassistant.backend.exception.DocumentNotFoundException;
import com.knowledgeassistant.backend.repository.DocumentRepository;
import com.knowledgeassistant.backend.repository.UserRepository;
import com.knowledgeassistant.backend.service.DocumentService;
import com.knowledgeassistant.backend.service.FileStorageService;
import com.knowledgeassistant.backend.service.RagIntegrationService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;
import java.util.UUID;

/**
 * Implementation of {@link DocumentService}.
 *
 * <p>Coordinates between file storage and the document database table.
 * Every query is scoped by user ID to enforce ownership isolation (USP #5).</p>
 */
@Service
public class DocumentServiceImpl implements DocumentService {

    private static final Logger log = LoggerFactory.getLogger(DocumentServiceImpl.class);

    private final DocumentRepository documentRepository;
    private final UserRepository userRepository;
    private final FileStorageService fileStorageService;
    private final RagIntegrationService ragIntegrationService;

    public DocumentServiceImpl(DocumentRepository documentRepository,
                               UserRepository userRepository,
                               FileStorageService fileStorageService,
                               RagIntegrationService ragIntegrationService) {
        this.documentRepository = documentRepository;
        this.userRepository = userRepository;
        this.fileStorageService = fileStorageService;
        this.ragIntegrationService = ragIntegrationService;
    }

    @Override
    @Transactional
    public DocumentResponse uploadDocument(MultipartFile file, UUID userId) {
        User owner = userRepository.findById(userId)
                .orElseThrow(() -> new DocumentNotFoundException("User not found"));

        String storedPath = fileStorageService.store(file, userId);

        Document document = Document.builder()
                .owner(owner)
                .filename(file.getOriginalFilename())
                .contentType(file.getContentType())
                .sizeBytes(file.getSize())
                .storagePath(storedPath)
                .build();

        Document saved = documentRepository.save(document);
        log.info("Document uploaded: id={}, user={}, file={}", saved.getId(), userId, saved.getFilename());

        // Asynchronously trigger the RAG processing pipeline
        ragIntegrationService.triggerProcessing(saved.getId(), userId, storedPath);

        return toResponse(saved);
    }

    @Override
    @Transactional(readOnly = true)
    public List<DocumentResponse> listDocuments(UUID userId) {
        return documentRepository.findByOwnerIdOrderByCreatedAtDesc(userId)
                .stream()
                .map(this::toResponse)
                .toList();
    }

    @Override
    @Transactional(readOnly = true)
    public DocumentResponse getDocument(UUID documentId, UUID userId) {
        Document document = documentRepository.findByIdAndOwnerId(documentId, userId)
                .orElseThrow(() -> new DocumentNotFoundException("Document not found"));
        return toResponse(document);
    }

    @Override
    @Transactional
    public void deleteDocument(UUID documentId, UUID userId) {
        Document document = documentRepository.findByIdAndOwnerId(documentId, userId)
                .orElseThrow(() -> new DocumentNotFoundException("Document not found"));

        fileStorageService.delete(document.getStoragePath());
        documentRepository.delete(document);
        log.info("Document deleted: id={}, user={}", documentId, userId);
    }

    private DocumentResponse toResponse(Document document) {
        return new DocumentResponse(
                document.getId(),
                document.getFilename(),
                document.getUploadStatus(),
                document.getSizeBytes(),
                document.getCreatedAt()
        );
    }
}
