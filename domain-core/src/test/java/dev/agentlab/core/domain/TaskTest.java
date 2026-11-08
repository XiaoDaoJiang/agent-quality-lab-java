package dev.agentlab.core.domain;

import java.util.UUID;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.NullAndEmptySource;
import org.junit.jupiter.params.provider.ValueSource;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;

class TaskTest {
    @Test
    void normalizesTitleAndStartsInTodo() {
        Task task = Task.create(UUID.randomUUID(), "  Improve quality  ");
        assertEquals("Improve quality", task.getTitle());
        assertEquals(TaskStatus.TODO, task.getStatus());
    }

    @ParameterizedTest
    @NullAndEmptySource
    @ValueSource(strings = {" ", "\t\n"})
    void rejectsBlankTitle(String title) {
        assertThrows(IllegalArgumentException.class, () -> Task.create(UUID.randomUUID(), title));
    }

    @Test
    void validatesBoundaryLength() {
        String boundary = repeat('a', 120);
        assertEquals(boundary, Task.create(UUID.randomUUID(), boundary).getTitle());
        assertThrows(IllegalArgumentException.class, () -> Task.create(UUID.randomUUID(), boundary + "b"));
    }

    @Test
    void rejectsNullIdentity() {
        assertThrows(NullPointerException.class, () -> Task.create(null, "task"));
    }

    @Test
    void completionIsIdempotentAndDoesNotMutateOriginal() {
        Task original = Task.create(UUID.randomUUID(), "task");
        Task done = original.complete();
        assertEquals(TaskStatus.TODO, original.getStatus());
        assertEquals(TaskStatus.DONE, done.getStatus());
        assertEquals(original.getId(), done.getId());
        assertSame(done, done.complete());
        assertThrows(IllegalStateException.class, done::cancel);
    }

    @Test
    void cancellationIsIdempotentAndTerminal() {
        Task cancelled = Task.create(UUID.randomUUID(), "task").cancel();
        assertSame(cancelled, cancelled.cancel());
        assertThrows(IllegalStateException.class, cancelled::complete);
    }

    private static String repeat(char value, int count) {
        StringBuilder result = new StringBuilder(count);
        for (int index = 0; index < count; index++) {
            result.append(value);
        }
        return result.toString();
    }
}
