package com.knowledgeassistant.backend.repository;

import com.knowledgeassistant.backend.entity.QaPair;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.UUID;

/** Persistence operations for question-answer pairs with their source citations. */
public interface QaPairRepository extends JpaRepository<QaPair, UUID> {
}
