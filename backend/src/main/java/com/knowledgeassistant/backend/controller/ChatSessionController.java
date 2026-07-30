package com.knowledgeassistant.backend.controller;

import com.knowledgeassistant.backend.config.CustomUserDetails;
import com.knowledgeassistant.backend.dto.chat.ChatSessionResponse;
import com.knowledgeassistant.backend.dto.chat.CreateSessionRequest;
import com.knowledgeassistant.backend.dto.chat.QaPairResponse;
import com.knowledgeassistant.backend.service.ChatService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

/** REST endpoints for managing chat sessions and viewing history. */
@RestController
@RequestMapping("/api/chat/sessions")
public class ChatSessionController {

    private final ChatService chatService;

    public ChatSessionController(ChatService chatService) {
        this.chatService = chatService;
    }

    /** Creates a new chat session for the authenticated user. */
    @PostMapping
    public ResponseEntity<ChatSessionResponse> createSession(
            @RequestBody(required = false) CreateSessionRequest request,
            @AuthenticationPrincipal CustomUserDetails principal) {
        ChatSessionResponse response = chatService.createSession(request, principal.getId());
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    /** Lists all chat sessions for the authenticated user. */
    @GetMapping
    public ResponseEntity<List<ChatSessionResponse>> listSessions(
            @AuthenticationPrincipal CustomUserDetails principal) {
        return ResponseEntity.ok(chatService.getUserSessions(principal.getId()));
    }

    /** Lists all Q&A pairs (chat history) for a specific session. */
    @GetMapping("/{id}/messages")
    public ResponseEntity<List<QaPairResponse>> getSessionMessages(
            @PathVariable UUID id,
            @AuthenticationPrincipal CustomUserDetails principal) {
        return ResponseEntity.ok(chatService.getSessionMessages(id, principal.getId()));
    }
}
