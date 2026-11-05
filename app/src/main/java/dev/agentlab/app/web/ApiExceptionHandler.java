package dev.agentlab.app.web;

import java.util.Collections;
import java.util.Map;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import dev.agentlab.core.domain.TaskNotFoundException;

@RestControllerAdvice
public final class ApiExceptionHandler {
    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<Map<String, String>> invalidArgument(IllegalArgumentException exception) {
        return response(HttpStatus.BAD_REQUEST, "INVALID_ARGUMENT");
    }

    @ExceptionHandler(TaskNotFoundException.class)
    public ResponseEntity<Map<String, String>> notFound(TaskNotFoundException exception) {
        return response(HttpStatus.NOT_FOUND, "TASK_NOT_FOUND");
    }

    @ExceptionHandler(IllegalStateException.class)
    public ResponseEntity<Map<String, String>> conflict(IllegalStateException exception) {
        return response(HttpStatus.CONFLICT, "INVALID_TRANSITION");
    }

    private static ResponseEntity<Map<String, String>> response(HttpStatus status, String code) {
        return ResponseEntity.status(status).body(Collections.singletonMap("code", code));
    }
}
