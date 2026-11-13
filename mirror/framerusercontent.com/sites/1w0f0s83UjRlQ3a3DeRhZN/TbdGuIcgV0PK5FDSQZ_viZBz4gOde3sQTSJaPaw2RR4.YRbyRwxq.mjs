import{t as e}from"./rolldown-runtime.Bi-D_2cA.mjs";async function t(e,t,i){let a=r[e],o=a?await a(t,i):void 0,s={bodyEnd:[],bodyStart:[],headEnd:[],headStart:[]};for(let t of n){if(t.pageIds&&!t.pageIds.has(e))continue;let n=t.code(o,i);n&&s[t.placement].push({...t,code:n})}return s}var n,r,i,a;function o(){return(o=e((()=>{n=[{code:(e,t)=>`<style>\r
input:-webkit-autofill,\r
input:-webkit-autofill:hover,\r
input:-webkit-autofill:focus,\r
textarea:-webkit-autofill,\r
textarea:-webkit-autofill:hover,\r
textarea:-webkit-autofill:focus {\r
    -webkit-text-fill-color: #C9D0D2 !important;\r
    -webkit-box-shadow: 0 0 0 1000px #000000 inset !important;\r
    box-shadow: 0 0 0 1000px #000000 inset !important;\r
    caret-color: #C9D0D2 !important;\r
}\r
</style>`,id:`NdC1PhkLO`,loadMode:`once`,name:`Form Auto-fill Color`,pageIds:/* @__PURE__ */ new Set([`Rgdzf7FfP`]),placement:`headEnd`},{code:(e,t)=>`<script>\r
(function () {\r
    function applyLanguage() {\r
        var language = /^\\/pl(?:\\/|$)/.test(location.pathname) ? "pl" : "en";\r
        if (document.documentElement.lang !== language) {\r
            document.documentElement.lang = language;\r
        }\r
    }\r
    applyLanguage();\r
    // Framer may update <html> during hydration. Keep the route's language.\r
    if (!window.__fragmentLanguageObserver && window.MutationObserver) {\r
        window.__fragmentLanguageObserver = new MutationObserver(applyLanguage);\r
        window.__fragmentLanguageObserver.observe(document.documentElement, {\r
            attributes: true,\r
            attributeFilter: ["lang"]\r
        });\r
    }\r
})();\r
<\/script>\r
`,id:`iD3FY04SN`,loadMode:`always`,name:`SEO lang`,placement:`headStart`},{code:(e,t)=>`<script>\r
(function () {\r
    var origin = "https://www.fragment.im";\r
\r
    function applyHreflang() {\r
        // Usuń automatyczne oznaczenia językowe Framera.\r
        Array.from(\r
            document.head.querySelectorAll(\r
                "link[data-framer-generated-hreflang][hreflang]"\r
            )\r
        ).forEach(function (link) {\r
            link.remove();\r
        });\r
\r
        var path = location.pathname.replace(/\\/+$/, "") || "/";\r
        var base = path.replace(/^\\/pl(?=\\/|$)/, "") || "/";\r
\r
        var robots = document.head.querySelectorAll(\r
            'meta[name="robots"], meta[name="googlebot"]'\r
        );\r
\r
        var excluded = Array.from(robots).some(function (meta) {\r
            return /\\b(noindex|none)\\b/i.test(meta.content);\r
        });\r
\r
        var urls = {\r
            en: origin + base,\r
            pl: origin + (base === "/" ? "/pl" : "/pl" + base)\r
        };\r
\r
        ["en", "pl"].forEach(function (language) {\r
            var selector =\r
                'link[data-fragment-hreflang="' + language + '"]';\r
\r
            var links = Array.from(\r
                document.head.querySelectorAll(selector)\r
            );\r
\r
            var link = links.shift();\r
\r
            links.forEach(function (duplicate) {\r
                duplicate.remove();\r
            });\r
\r
            if (excluded) {\r
                if (link) link.remove();\r
                return;\r
            }\r
\r
            if (!link) {\r
                link = document.createElement("link");\r
                link.setAttribute("data-fragment-hreflang", language);\r
                link.rel = "alternate";\r
                link.hreflang = language;\r
                link.href = urls[language];\r
                document.head.appendChild(link);\r
                return;\r
            }\r
\r
            if (link.rel !== "alternate") link.rel = "alternate";\r
            if (link.hreflang !== language) link.hreflang = language;\r
            if (link.href !== urls[language]) link.href = urls[language];\r
        });\r
    }\r
\r
    if (window.__fragmentHreflangObserver) {\r
        window.__fragmentHreflangObserver.disconnect();\r
    }\r
\r
    applyHreflang();\r
\r
    window.__fragmentHreflangObserver = new MutationObserver(\r
        applyHreflang\r
    );\r
\r
    window.__fragmentHreflangObserver.observe(document.head, {\r
        childList: true,\r
        subtree: true,\r
        attributes: true,\r
        attributeFilter: ["content", "href", "hreflang", "rel"]\r
    });\r
})();\r
<\/script>`,id:`DUTaksmog`,loadMode:`always`,name:`SEO hreflang`,placement:`headEnd`}],r={},i={bodyEnd:[],bodyStart:[],headEnd:[`NdC1PhkLO`,`DUTaksmog`],headStart:[`UNPc32xLe`,`DBRVX768U`,`mo9XI5_Zp`,`w55AE8w4z`,`iD3FY04SN`,`TNm6eBKh3`]},a={exports:{getSnippets:{type:`function`,isAsync:!0,annotations:{framerContractVersion:`1`}},snippetsSorting:{type:`variable`,annotations:{framerContractVersion:`1`}},__FramerMetadata__:{type:`variable`}}}})))()}o();export{a as __FramerMetadata__,t as getSnippets,i as snippetsSorting};
//# sourceMappingURL=TbdGuIcgV0PK5FDSQZ_viZBz4gOde3sQTSJaPaw2RR4.YRbyRwxq.mjs.map