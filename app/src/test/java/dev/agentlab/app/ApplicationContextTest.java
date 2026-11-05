package dev.agentlab.app;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import dev.agentlab.core.application.TaskService;

import static org.junit.jupiter.api.Assertions.assertNotNull;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.NONE)
class ApplicationContextTest {
    @Autowired
    private TaskService taskService;

    @Test
    void applicationWiresItsRealService() {
        assertNotNull(taskService);
    }
}
