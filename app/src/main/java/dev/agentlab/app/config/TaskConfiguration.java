package dev.agentlab.app.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import dev.agentlab.core.adapter.InMemoryTaskRepository;
import dev.agentlab.core.application.TaskService;

@Configuration(proxyBeanMethods = false)
public class TaskConfiguration {
    @Bean
    public TaskService taskService() {
        return new TaskService(new InMemoryTaskRepository());
    }
}
