package com.knowledgeassistant.backend.dto;

import jakarta.validation.constraints.NotBlank;

/** Payload for token refresh. */
public record RefreshRequest(
        @NotBlank String refreshToken
) {}
