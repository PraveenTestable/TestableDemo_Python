/**
 * Whitebox verification harness — exercises decision paths and logical combinations.
 */

const { routeRequest, evaluateFlags } = require("./router");

function verifyRouteRequestPaths() {
  assert(routeRequest("DELETE", true, false) === "405");
  assert(routeRequest("PATCH", false, false) === "405");

  assert(routeRequest("GET", true, false) === "200-read");
  assert(routeRequest("POST", true, false) === "201-created");
  assert(routeRequest("PUT", true, false) === "202-accepted");

  assert(routeRequest("GET", false, false) === "401-unauthorized");
  assert(routeRequest("GET", true, true) === "401-unauthorized");
  assert(routeRequest("POST", false, true) === "401-unauthorized");
}

function verifyEvaluateFlagsCombinations() {
  assert(evaluateFlags(true, true, false) === "path-alpha");
  assert(evaluateFlags(true, true, true) === "path-alpha");
  assert(evaluateFlags(true, false, true) === "path-alpha");
  assert(evaluateFlags(true, false, false) === "path-alpha");

  assert(evaluateFlags(false, true, false) === "path-beta");
  assert(evaluateFlags(false, true, true) === "path-beta");
  assert(evaluateFlags(false, false, true) === "path-beta");

  assert(evaluateFlags(false, false, false) === "path-default");
}

function verifyCompoundConditions() {
  assert(routeRequest("GET", true, !false) === "401-unauthorized");
  assert(routeRequest("GET", true, !true) === "200-read");
  assert(evaluateFlags(!false, !false, !true) === "path-alpha");
  assert(evaluateFlags(!true, !false, !false) === "path-beta");
}

function runAllVerifications() {
  verifyRouteRequestPaths();
  verifyEvaluateFlagsCombinations();
  verifyCompoundConditions();
}

module.exports = { runAllVerifications };
