package com.knowledgeassistant.backend.dto;

import com.knowledgeassistant.backend.entity.UploadStatus;

import java.time.Instant;
import java.util.UUID;

/** Client-facing representation of a document — never exposes the physical storage path. */
public record DocumentResponse(
        UUID id,
        String filename,
        UploadStatus uploadStatus,
        Long fileSizeBytes,
        Instant createdAt
) {
}
