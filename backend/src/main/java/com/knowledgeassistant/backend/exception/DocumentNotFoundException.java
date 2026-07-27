package com.knowledgeassistant.backend.exception;

/** Thrown when a document cannot be found or is not owned by the requesting user. */
public class DocumentNotFoundException extends RuntimeException {

    public DocumentNotFoundException(String message) {
        super(message);
    }
}
