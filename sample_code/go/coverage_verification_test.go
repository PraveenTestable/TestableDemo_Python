package demo

import "testing"

// Whitebox verification harness — exercises decision paths and logical combinations.

func verifyRouteRequestPaths(t *testing.T) {
	t.Run("invalid method", func(t *testing.T) {
		assertEqual(t, RouteRequest("DELETE", true, false), "405")
		assertEqual(t, RouteRequest("PATCH", false, false), "405")
	})
	t.Run("authenticated routes", func(t *testing.T) {
		assertEqual(t, RouteRequest("GET", true, false), "200-read")
		assertEqual(t, RouteRequest("POST", true, false), "201-created")
		assertEqual(t, RouteRequest("PUT", true, false), "202-accepted")
	})
	t.Run("unauthorized routes", func(t *testing.T) {
		assertEqual(t, RouteRequest("GET", false, false), "401-unauthorized")
		assertEqual(t, RouteRequest("GET", true, true), "401-unauthorized")
		assertEqual(t, RouteRequest("POST", false, true), "401-unauthorized")
	})
}

func verifyEvaluateFlagsCombinations(t *testing.T) {
	t.Run("path alpha", func(t *testing.T) {
		assertEqual(t, EvaluateFlags(true, true, false), "path-alpha")
		assertEqual(t, EvaluateFlags(true, true, true), "path-alpha")
		assertEqual(t, EvaluateFlags(true, false, true), "path-alpha")
		assertEqual(t, EvaluateFlags(true, false, false), "path-alpha")
	})
	t.Run("path beta", func(t *testing.T) {
		assertEqual(t, EvaluateFlags(false, true, false), "path-beta")
		assertEqual(t, EvaluateFlags(false, true, true), "path-beta")
		assertEqual(t, EvaluateFlags(false, false, true), "path-beta")
	})
	t.Run("path default", func(t *testing.T) {
		assertEqual(t, EvaluateFlags(false, false, false), "path-default")
	})
}

func verifyCompoundConditions(t *testing.T) {
	t.Run("compound logic", func(t *testing.T) {
		assertEqual(t, RouteRequest("GET", true, false == true), "401-unauthorized")
		assertEqual(t, RouteRequest("GET", true, false == false), "200-read")
		assertEqual(t, EvaluateFlags(true, true, false == true), "path-alpha")
		assertEqual(t, EvaluateFlags(false, true, false == false), "path-beta")
	})
}

func assertEqual(t *testing.T, got, want string) {
	t.Helper()
	if got != want {
		t.Fatalf("got %q, want %q", got, want)
	}
}

func RunAllVerifications(t *testing.T) {
	verifyRouteRequestPaths(t)
	verifyEvaluateFlagsCombinations(t)
	verifyCompoundConditions(t)
}
