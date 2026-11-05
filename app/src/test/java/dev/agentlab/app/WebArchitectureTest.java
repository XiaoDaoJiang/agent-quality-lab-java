package dev.agentlab.app;

import org.junit.jupiter.api.Test;

import com.tngtech.archunit.core.domain.JavaClasses;
import com.tngtech.archunit.core.importer.ClassFileImporter;
import com.tngtech.archunit.core.importer.ImportOption;
import com.tngtech.archunit.lang.ArchRule;

import dev.agentlab.app.fixtures.web.BadController;

import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.noClasses;
import static org.junit.jupiter.api.Assertions.assertThrows;

class WebArchitectureTest {
    private static final ArchRule WEB_RULE = noClasses().that().resideInAPackage("..web..")
            .should().dependOnClassesThat().resideInAnyPackage("..ports..", "..adapter..");
    @Test
    void controllersCannotAccessRepositories() {
        JavaClasses classes = new ClassFileImporter()
                .withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_TESTS).importPackages("dev.agentlab.app");
        WEB_RULE.check(classes);
    }
    @Test
    void ruleReallyRejectsARepositoryDependency() {
        JavaClasses bad = new ClassFileImporter().importClasses(BadController.class);
        assertThrows(AssertionError.class, () -> WEB_RULE.check(bad));
    }
}
