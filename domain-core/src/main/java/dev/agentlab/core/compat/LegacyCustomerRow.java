package dev.agentlab.core.compat;

/** Frozen public field contract used to demonstrate one scoped legacy baseline. */
public final class LegacyCustomerRow {
    public final String customer_name;

    public LegacyCustomerRow(String customerName) {
        this.customer_name = customerName;
    }
}
