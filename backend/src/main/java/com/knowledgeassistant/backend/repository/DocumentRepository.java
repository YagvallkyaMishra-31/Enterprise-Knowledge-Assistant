package com.knowledgeassistant.backend.repository;

import com.knowledgeassistant.backend.entity.Document;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

/** Persistence operations for uploaded documents, scoped by user ownership. */
public interface DocumentRepository extends JpaRepository<Document, UUID> {

    /** Returns all documents owned by the given user, newest first. */
    List<Document> findByOwnerIdOrderByCreatedAtDesc(UUID userId);

    /** Returns a document only if it belongs to the given user. */
    Optional<Document> findByIdAndOwnerId(UUID id, UUID userId);
}
