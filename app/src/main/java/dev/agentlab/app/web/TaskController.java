package dev.agentlab.app.web;

import java.net.URI;
import java.util.UUID;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import dev.agentlab.core.application.TaskService;
import dev.agentlab.core.domain.Task;

@RestController
@RequestMapping("/api/tasks")
public final class TaskController {
    private final TaskService service;

    public TaskController(TaskService service) {
        this.service = service;
    }

    @PostMapping
    public ResponseEntity<Task> create(@RequestBody CreateTaskRequest request) {
        Task task = service.create(request.getTitle());
        return ResponseEntity.created(URI.create("/api/tasks/" + task.getId())).body(task);
    }

    @GetMapping("/{id}")
    public Task get(@PathVariable("id") UUID id) {
        return service.get(id);
    }

    @PostMapping("/{id}/complete")
    public Task complete(@PathVariable("id") UUID id) {
        return service.complete(id);
    }

    @PostMapping("/{id}/cancel")
    public Task cancel(@PathVariable("id") UUID id) {
        return service.cancel(id);
    }
}
