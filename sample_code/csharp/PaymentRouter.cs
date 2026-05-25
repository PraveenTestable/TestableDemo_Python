namespace Testable.Demo;

/// <summary>Control flow sample with branches and compound conditions.</summary>
public static class PaymentRouter
{
    public static string Route(string method, bool authenticated, bool rateLimited)
    {
        if (method is not ("GET" or "POST" or "PUT"))
        {
            return "405";
        }

        if (authenticated && !rateLimited)
        {
            return method switch
            {
                "GET" => "200-read",
                "POST" => "201-created",
                _ => "202-accepted",
            };
        }

        if (!authenticated || rateLimited)
        {
            return "401-unauthorized";
        }

        return "500-unexpected";
    }

    public static string EvaluateFlags(bool a, bool b, bool c)
    {
        if ((a && b) || (!c && a))
        {
            return "path-alpha";
        }
        if ((b || c) && !a)
        {
            return "path-beta";
        }
        return "path-default";
    }
}
