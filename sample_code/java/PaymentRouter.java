package com.testable.demo;

public class PaymentRouter {

    public String route(String method, boolean authenticated, boolean rateLimited) {
        if (!method.equals("GET") && !method.equals("POST") && !method.equals("PUT")) {
            return "405";
        }

        if (authenticated && !rateLimited) {
            switch (method) {
                case "GET":
                    return "200-read";
                case "POST":
                    return "201-created";
                default:
                    return "202-accepted";
            }
        }

        if (!authenticated || rateLimited) {
            return "401-unauthorized";
        }

        return "500-unexpected";
    }

    public String evaluateFlags(boolean a, boolean b, boolean c) {
        if ((a && b) || (!c && a)) {
            return "path-alpha";
        }
        if ((b || c) && !a) {
            return "path-beta";
        }
        return "path-default";
    }
}
