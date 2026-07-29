package com.knowledgeassistant.backend.entity;

/** Lifecycle state of a document from upload through chunking. */
public enum UploadStatus {
    PENDING,
    PROCESSING,
    READY,
    FAILED
}
