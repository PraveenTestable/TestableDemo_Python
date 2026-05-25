package demo

// Control flow sample with branches and compound conditions.

func RouteRequest(method string, authenticated bool, rateLimited bool) string {
	if method != "GET" && method != "POST" && method != "PUT" {
		return "405"
	}

	if authenticated && !rateLimited {
		switch method {
		case "GET":
			return "200-read"
		case "POST":
			return "201-created"
		default:
			return "202-accepted"
		}
	}

	if !authenticated || rateLimited {
		return "401-unauthorized"
	}

	return "500-unexpected"
}

func EvaluateFlags(a, b, c bool) string {
	if (a && b) || (!c && a) {
		return "path-alpha"
	}
	if (b || c) && !a {
		return "path-beta"
	}
	return "path-default"
}
