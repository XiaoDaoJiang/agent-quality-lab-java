package dev.agentlab.core.architecture;

import java.io.DataInputStream;
import java.io.InputStream;

import org.junit.jupiter.api.Test;

import dev.agentlab.core.domain.Task;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

class BytecodeCompatibilityTest {
    @Test
    void coreClassFilesTargetJava8() throws Exception {
        try (InputStream stream = Task.class.getResourceAsStream("Task.class")) {
            assertNotNull(stream);
            try (DataInputStream input = new DataInputStream(stream)) {
                assertEquals(0xCAFEBABE, input.readInt());
                input.readUnsignedShort();
                assertEquals(52, input.readUnsignedShort());
            }
        }
    }

    @Test
    void testRuntimeMatchesSelectedLane() {
        String expected = System.getProperty("lab.expectedJava");
        String actual = System.getProperty("java.specification.version");
        assertNotNull(expected);
        assertEquals("1.8".equals(expected) ? "8" : expected, "1.8".equals(actual) ? "8" : actual);
    }
}
