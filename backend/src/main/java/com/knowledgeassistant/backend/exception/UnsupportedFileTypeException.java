package com.knowledgeassistant.backend.exception;

/** Thrown when an uploaded file's extension is not in the allowed list. */
public class UnsupportedFileTypeException extends RuntimeException {

    public UnsupportedFileTypeException(String message) {
        super(message);
    }
}
