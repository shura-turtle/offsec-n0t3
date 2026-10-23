---
title: "GraphQL · Schema to Resolver"
weight: 51
bookToc: true
---

# GraphQL manual testing

**Endpoint → valid operation → schema → exact fields/arguments → resolver authorization.** Introspection reveals structure; it does not by itself grant access.

## 1. Find and confirm

Look in frontend network requests before trying common `/graphql`, `/api/graphql`, `/gql` paths. A GraphiQL/Apollo UI may show history or schema documentation.

```http
POST /graphql HTTP/1.1
Host: ctf.invalid
Content-Type: application/json

{"query":"query { __typename }"}
```

Expected example: `{"data":{"__typename":"Query"}}`. A `200 OK` response may still contain an `errors` array. GraphQL field errors can coexist with partial `data`.

Raw GraphQL and JSON-wrapped requests are different transports. Some servers accept `application/graphql`; others accept only JSON. Follow a known working client request.

## 2. Inspect root operation names

```graphql
query {
  __schema {
    queryType { name }
    mutationType { name }
    subscriptionType { name }
  }
}
```

Then list types:

```graphql
query {
  __schema { types { name kind description } }
}
```

Do not assume the query root is literally named `Query`; use the actual returned name.

## 3. Inspect fields, arguments and wrappers

```graphql
query {
  __type(name: "Query") {
    fields(includeDeprecated: true) {
      name
      args {
        name
        defaultValue
        type { kind name ofType { kind name ofType { kind name } } }
      }
      type { kind name ofType { kind name ofType { kind name } } }
    }
  }
}
```

Replace `Query` with the root name from step 2. `NON_NULL` and `LIST` wrappers often have no `name`; follow `ofType`. Add more nested `ofType` levels if needed. Inspect returned object/input types by name:

```graphql
query {
  __type(name: "User") { fields { name type { kind name } } }
  __type(name: "UpdateUserInput") {
    inputFields { name type { kind name ofType { kind name } } }
  }
}
```

If this schema lacks those names, request returns null rather than discovering them automatically.

## 4. If introspection is disabled

Use frontend operations, JS source maps, provided schema files, GraphiQL docs and validation errors. A typo can expose suggestions:

```graphql
query { usre { id } }
```

Some servers suggest `user`; others suppress suggestions. This is a clue, not a complete enumeration strategy. Do not confuse `__typename` being available with full introspection being enabled. Persisted-query deployments may require known operation IDs; inspect client requests instead of assuming arbitrary queries are allowed.

## 5. Authorization through direct and nested resolvers

Example only after enumerating matching fields:

```graphql
query {
  user(id: "ACCOUNT_A_ID") { id username privateNote }
}
```

Send using A's token, B's token and no token. Then test alternate paths to the same object:

```graphql
query {
  project(id: "A_PROJECT_ID") {
    owner { id username privateNote }
  }
}
```

One root resolver can enforce access while a nested resolver leaks the same private field. The requested field must be intended private; normal public usernames are not enough to prove IDOR.

## 6. Global node IDs

If the schema exposes `node(id: ID!)`, inspect actual IDs from your own objects. A Base64 ID may encode `User:12`; another may be an opaque UUID. Encoding is not access control.

```graphql
query {
  node(id: "ENUMERATED_OR_ADAPTED_ID") {
    __typename
    ... on User { id username privateNote }
  }
}
```

Inline fragments need a real schema type name and fields allowed on it. A null result can mean nonexistent object, wrong ID format, or authorization; compare known A/B IDs.

## 7. Variables and hidden input fields

```http
POST /graphql HTTP/1.1
Host: ctf.invalid
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{"query":"mutation Change($input: UpdateUserInput!) { updateUser(input:$input) { id role } }","variables":{"input":{"displayName":"ctf-player","role":"ADMIN"}},"operationName":"Change"}
```

All names above are schema-dependent. GraphQL usually rejects unknown input fields, so introspection or source is useful. Test only your own account and verify role through a protected backend action. A selectable `role` field is not automatically writable; enum values are case-sensitive.

## 8. Aliases, batching and per-operation limits

A small comparison can show whether checks are applied per operation or only per HTTP request:

```graphql
query {
  mine: user(id: "ACCOUNT_B_ID") { id username }
  other: user(id: "ACCOUNT_A_ID") { id username privateNote }
}
```

Aliases rename response keys; they do not inherently bypass authorization. Some servers accept JSON arrays of operations, others reject HTTP batching. Keep manual comparisons small; large alias/depth tests may only exhaust resources and are not needed to prove an authorization flaw.

A mutation document can contain multiple fields executed serially, but that is not a general concurrency/race primitive. Resolvers can still have independent state flaws; inspect actual response data and state.

## 9. Errors and neighboring techniques

| Error/result | Meaning / next step |
| --- | --- |
| `Cannot query field ...` | Wrong field/type; inspect schema/client |
| `must have a selection of subfields` | Object return needs `{ ... }` |
| `must not have a selection` | Scalar/enum return; remove subfields |
| Variable type mismatch | Preserve ID/Int/String and non-null requirements |
| `errors` plus partial `data` | Check each returned field; don't compare status alone |
| Valid query but forbidden field | Resolver authorization active at that path |
| Query argument triggers SQL/URL/file behavior | Follow [SQLi](../sqli/), [SSRF](../ssrf/) or [LFI](../lfi-traversal/) at that resolver |

Cookie-authenticated GraphQL accepting form bodies or GET mutations may also introduce [CSRF](../csrf-cors/). A JSON-only route with enforced content type and preflight requirements is a different case.

## Tool workflow

Use [Burp Community Repeater](../../ajcbbc_allow_tools/burp_suite_community/) for paired manual requests. Keep the baseline in one tab and change one input in another. Browser-only behavior such as XSS, cookies and CORS still needs a real browser proof.

## References

[GraphQL introspection](https://graphql.org/learn/introspection/), [GraphQL serving over HTTP](https://graphql.org/learn/serving-over-http/), [GraphQL authorization](https://graphql.org/learn/authorization/), [GraphQL operations](https://graphql.org/learn/queries/).
