using System.Diagnostics;

namespace Testable.Demo;

/// <summary>Whitebox verification harness — exercises decision paths and logical combinations.</summary>
public static class CoverageVerification
{
    public static void VerifyRouteRequestPaths()
    {
        Debug.Assert(PaymentRouter.Route("DELETE", true, false) == "405");
        Debug.Assert(PaymentRouter.Route("PATCH", false, false) == "405");

        Debug.Assert(PaymentRouter.Route("GET", true, false) == "200-read");
        Debug.Assert(PaymentRouter.Route("POST", true, false) == "201-created");
        Debug.Assert(PaymentRouter.Route("PUT", true, false) == "202-accepted");

        Debug.Assert(PaymentRouter.Route("GET", false, false) == "401-unauthorized");
        Debug.Assert(PaymentRouter.Route("GET", true, true) == "401-unauthorized");
        Debug.Assert(PaymentRouter.Route("POST", false, true) == "401-unauthorized");
    }

    public static void VerifyEvaluateFlagsCombinations()
    {
        Debug.Assert(PaymentRouter.EvaluateFlags(true, true, false) == "path-alpha");
        Debug.Assert(PaymentRouter.EvaluateFlags(true, true, true) == "path-alpha");
        Debug.Assert(PaymentRouter.EvaluateFlags(true, false, true) == "path-alpha");
        Debug.Assert(PaymentRouter.EvaluateFlags(true, false, false) == "path-alpha");

        Debug.Assert(PaymentRouter.EvaluateFlags(false, true, false) == "path-beta");
        Debug.Assert(PaymentRouter.EvaluateFlags(false, true, true) == "path-beta");
        Debug.Assert(PaymentRouter.EvaluateFlags(false, false, true) == "path-beta");

        Debug.Assert(PaymentRouter.EvaluateFlags(false, false, false) == "path-default");
    }

    public static void VerifyCompoundConditions()
    {
        Debug.Assert(PaymentRouter.Route("GET", true, !false) == "401-unauthorized");
        Debug.Assert(PaymentRouter.Route("GET", true, !true) == "200-read");
        Debug.Assert(PaymentRouter.EvaluateFlags(!false, !false, !true) == "path-alpha");
        Debug.Assert(PaymentRouter.EvaluateFlags(!true, !false, !false) == "path-beta");
    }

    public static void RunAllVerifications()
    {
        VerifyRouteRequestPaths();
        VerifyEvaluateFlagsCombinations();
        VerifyCompoundConditions();
    }
}
