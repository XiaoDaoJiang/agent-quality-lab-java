package dev.agentlab.app;

import java.util.UUID;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import dev.agentlab.core.adapter.InMemoryTaskRepository;
import dev.agentlab.core.application.TaskService;
import dev.agentlab.app.web.ApiExceptionHandler;
import dev.agentlab.app.web.TaskController;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

class TaskHttpTest {
    private MockMvc mvc;

    @BeforeEach
    void setUp() {
        mvc = MockMvcBuilders.standaloneSetup(new TaskController(new TaskService(new InMemoryTaskRepository())))
                .setControllerAdvice(new ApiExceptionHandler()).build();
    }

    @Test
    void createGetCompleteAndRejectCancellation() throws Exception {
        String body = mvc.perform(post("/api/tasks").contentType(MediaType.APPLICATION_JSON)
                .content("{\"title\":\"Add quality gate\"}"))
                .andExpect(status().isCreated()).andExpect(jsonPath("$.status").value("TODO"))
                .andReturn().getResponse().getContentAsString();
        JsonNode created = new ObjectMapper().readTree(body);
        String path = "/api/tasks/" + created.get("id").asText();
        mvc.perform(get(path)).andExpect(status().isOk());
        mvc.perform(post(path + "/complete")).andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("DONE"));
        mvc.perform(post(path + "/complete")).andExpect(status().isOk());
        mvc.perform(post(path + "/cancel")).andExpect(status().isConflict())
                .andExpect(jsonPath("$.code").value("INVALID_TRANSITION"));
    }

    @Test
    void invalidTitleReturns400() throws Exception {
        mvc.perform(post("/api/tasks").contentType(MediaType.APPLICATION_JSON).content("{\"title\":\"  \"}"))
                .andExpect(status().isBadRequest()).andExpect(jsonPath("$.code").value("INVALID_ARGUMENT"));
    }

    @Test
    void missingTaskReturns404() throws Exception {
        mvc.perform(get("/api/tasks/" + UUID.randomUUID())).andExpect(status().isNotFound());
    }

    @Test
    void missingBodyReturns400() throws Exception {
        mvc.perform(post("/api/tasks").contentType(MediaType.APPLICATION_JSON)).andExpect(status().isBadRequest());
    }
}
