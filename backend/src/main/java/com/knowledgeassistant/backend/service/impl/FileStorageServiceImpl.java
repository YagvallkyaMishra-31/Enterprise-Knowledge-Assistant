package com.knowledgeassistant.backend.service.impl;

import com.knowledgeassistant.backend.exception.FileStorageException;
import com.knowledgeassistant.backend.exception.FileTooLargeException;
import com.knowledgeassistant.backend.exception.UnsupportedFileTypeException;
import com.knowledgeassistant.backend.service.FileStorageService;
import jakarta.annotation.PostConstruct;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.util.List;
import java.util.UUID;

/**
 * Local-disk implementation of {@link FileStorageService}.
 *
 * <p>Files are stored as {@code {upload-root}/{userId}/{uuid}-{sanitized-filename}}.
 * The root directory is created on startup if it does not exist.</p>
 */
@Service
public class FileStorageServiceImpl implements FileStorageService {

    private static final Logger log = LoggerFactory.getLogger(FileStorageServiceImpl.class);

    private final Path rootPath;
    private final long maxSizeBytes;
    private final List<String> allowedExtensions;

    public FileStorageServiceImpl(
            @Value("${app.upload.root-path}") String rootPathStr,
            @Value("${app.upload.max-size-mb}") int maxSizeMb,
            @Value("${app.upload.allowed-extensions}") List<String> allowedExtensions) {
        this.rootPath = Paths.get(rootPathStr).toAbsolutePath().normalize();
        this.maxSizeBytes = (long) maxSizeMb * 1024 * 1024;
        this.allowedExtensions = allowedExtensions.stream()
                .map(ext -> ext.toLowerCase().trim())
                .toList();
    }

    @PostConstruct
    void init() {
        try {
            Files.createDirectories(rootPath);
            log.info("Upload root directory ready: {}", rootPath);
        } catch (IOException e) {
            throw new FileStorageException("Could not create upload root directory: " + rootPath, e);
        }
    }

    @Override
    public String store(MultipartFile file, UUID userId) {
        String originalFilename = file.getOriginalFilename();
        if (originalFilename == null || originalFilename.isBlank()) {
            throw new UnsupportedFileTypeException("Uploaded file has no filename");
        }

        String extension = extractExtension(originalFilename);
        if (!allowedExtensions.contains(extension.toLowerCase())) {
            throw new UnsupportedFileTypeException(
                    "File type '." + extension + "' is not allowed. Accepted: " + allowedExtensions);
        }

        if (file.getSize() > maxSizeBytes) {
            throw new FileTooLargeException(
                    "File size " + file.getSize() + " bytes exceeds maximum of " + maxSizeBytes + " bytes");
        }

        String sanitized = sanitizeFilename(originalFilename);
        String storedName = UUID.randomUUID() + "-" + sanitized;
        Path userDir = rootPath.resolve(userId.toString());
        Path targetPath = userDir.resolve(storedName).normalize();

        if (!targetPath.startsWith(rootPath)) {
            throw new FileStorageException("Path traversal attempt detected", null);
        }

        try {
            Files.createDirectories(userDir);
            try (InputStream inputStream = file.getInputStream()) {
                Files.copy(inputStream, targetPath, StandardCopyOption.REPLACE_EXISTING);
            }
            log.info("Stored file: {}", targetPath);
            return userId + "/" + storedName;
        } catch (IOException e) {
            throw new FileStorageException("Failed to store file: " + originalFilename, e);
        }
    }

    @Override
    public void delete(String storedPath) {
        Path filePath = rootPath.resolve(storedPath).normalize();

        if (!filePath.startsWith(rootPath)) {
            throw new FileStorageException("Path traversal attempt detected", null);
        }

        try {
            boolean deleted = Files.deleteIfExists(filePath);
            if (deleted) {
                log.info("Deleted file: {}", filePath);
            } else {
                log.warn("File not found for deletion: {}", filePath);
            }
        } catch (IOException e) {
            throw new FileStorageException("Failed to delete file: " + storedPath, e);
        }
    }

    private String extractExtension(String filename) {
        int dotIndex = filename.lastIndexOf('.');
        if (dotIndex < 0 || dotIndex == filename.length() - 1) {
            return "";
        }
        return filename.substring(dotIndex + 1);
    }

    private String sanitizeFilename(String filename) {
        return filename.replaceAll("[^a-zA-Z0-9._-]", "_");
    }
}
