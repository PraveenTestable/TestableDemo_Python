package com.testable.demo;

/** Whitebox verification harness — exercises decision paths and logical combinations. */
public final class CoverageVerification {

    private CoverageVerification() {}

    public static void verifyRouteRequestPaths() {
        assert "405".equals(new PaymentRouter().route("DELETE", true, false));
        assert "405".equals(new PaymentRouter().route("PATCH", false, false));

        assert "200-read".equals(new PaymentRouter().route("GET", true, false));
        assert "201-created".equals(new PaymentRouter().route("POST", true, false));
        assert "202-accepted".equals(new PaymentRouter().route("PUT", true, false));

        assert "401-unauthorized".equals(new PaymentRouter().route("GET", false, false));
        assert "401-unauthorized".equals(new PaymentRouter().route("GET", true, true));
        assert "401-unauthorized".equals(new PaymentRouter().route("POST", false, true));
    }

    public static void verifyEvaluateFlagsCombinations() {
        PaymentRouter router = new PaymentRouter();
        assert "path-alpha".equals(router.evaluateFlags(true, true, false));
        assert "path-alpha".equals(router.evaluateFlags(true, true, true));
        assert "path-alpha".equals(router.evaluateFlags(true, false, true));
        assert "path-alpha".equals(router.evaluateFlags(true, false, false));

        assert "path-beta".equals(router.evaluateFlags(false, true, false));
        assert "path-beta".equals(router.evaluateFlags(false, true, true));
        assert "path-beta".equals(router.evaluateFlags(false, false, true));

        assert "path-default".equals(router.evaluateFlags(false, false, false));
    }

    public static void verifyCompoundConditions() {
        PaymentRouter router = new PaymentRouter();
        assert "401-unauthorized".equals(router.route("GET", true, !false == false));
        assert "200-read".equals(router.route("GET", true, !true == false));
        assert "path-alpha".equals(router.evaluateFlags(!false, !false, !true));
        assert "path-beta".equals(router.evaluateFlags(!true, !false, !false));
    }

    public static void runAllVerifications() {
        verifyRouteRequestPaths();
        verifyEvaluateFlagsCombinations();
        verifyCompoundConditions();
    }
}
