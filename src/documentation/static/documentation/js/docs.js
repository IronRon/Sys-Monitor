import mermaid from
    "https://cdn.jsdelivr.net/npm/mermaid@11.16.1/dist/mermaid.esm.min.mjs";


function prepareMermaidBlocks() {

    const blocks =
        document.querySelectorAll(
            "pre > code.language-mermaid"
        );


    blocks.forEach((codeBlock) => {

        const oldPre =
            codeBlock.parentElement;


        const mermaidBlock =
            document.createElement("pre");


        mermaidBlock.classList.add(
            "mermaid"
        );


        mermaidBlock.textContent =
            codeBlock.textContent;


        oldPre.replaceWith(
            mermaidBlock
        );
    });
}


async function renderDiagrams() {

    prepareMermaidBlocks();


    mermaid.initialize({
        startOnLoad: false,
        theme: "dark",
        securityLevel: "strict",
    });


    await mermaid.run({
        querySelector: ".mermaid",
    });
}


renderDiagrams();