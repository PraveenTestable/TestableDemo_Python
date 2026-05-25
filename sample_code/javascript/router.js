/**
 * Control flow sample with branches and compound conditions.
 */

function routeRequest(method, authenticated, rateLimited) {
  if (!["GET", "POST", "PUT"].includes(method)) {
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

function evaluateFlags(a, b, c) {
  if ((a && b) || (!c && a)) {
    return "path-alpha";
  }
  if ((b || c) && !a) {
    return "path-beta";
  }
  return "path-default";
}

module.exports = { routeRequest, evaluateFlags };
