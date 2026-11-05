package dev.agentlab.core.architecture;

import org.junit.jupiter.api.Test;

import com.tngtech.archunit.core.domain.JavaClasses;
import com.tngtech.archunit.core.importer.ClassFileImporter;
import com.tngtech.archunit.core.importer.ImportOption;
import com.tngtech.archunit.lang.ArchRule;

import dev.agentlab.fixtures.domain.BadDomain;

import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.noClasses;
import static org.junit.jupiter.api.Assertions.assertThrows;

class CoreArchitectureTest {
    private static final ArchRule DOMAIN_RULE = noClasses().that().resideInAPackage("..domain..")
            .should().dependOnClassesThat().resideInAnyPackage("..adapter..", "..application..",
                    "..ports..", "org.springframework..");
    private final JavaClasses classes = new ClassFileImporter()
            .withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_TESTS)
            .importPackages("dev.agentlab.core");

    @Test
    void domainDoesNotDependOnInfrastructureOrApplication() {
        DOMAIN_RULE.check(classes);
    }

    @Test
    void rejectsKnownArchitectureViolation() {
        JavaClasses bad = new ClassFileImporter().importClasses(BadDomain.class);
        assertThrows(AssertionError.class, () -> DOMAIN_RULE.check(bad));
    }

    @Test
    void applicationUsesPortsInsteadOfConcreteAdapters() {
        noClasses().that().resideInAPackage("..application..")
                .should().dependOnClassesThat().resideInAnyPackage("..adapter..", "org.springframework..")
                .check(classes);
    }

    @Test
    void coreHasNoSpringOrWebRuntimeDependency() {
        noClasses().should().dependOnClassesThat()
                .resideInAnyPackage("org.springframework..", "jakarta.servlet..", "javax.servlet..")
                .check(classes);
    }
}
