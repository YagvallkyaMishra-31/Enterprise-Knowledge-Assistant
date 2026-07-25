package com.knowledgeassistant.backend.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;

/** Payload for user login. */
public record LoginRequest(
        @NotBlank @Email String email,
        @NotBlank String password
) {}
