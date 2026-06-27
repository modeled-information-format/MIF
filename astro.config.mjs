import { defineConfig } from "astro/config";
import starlight from "@astrojs/starlight";
import starlightLlmsTxt from "starlight-llms-txt";
import astroMermaid from "astro-mermaid";

export default defineConfig({
  site: "https://mif-spec.dev",
  integrations: [
    astroMermaid(),
    starlight({
      plugins: [starlightLlmsTxt()],
      title: "MIF",
      customCss: ["./src/styles/mif-brand.css"],
      logo: {
        light: "./src/assets/logo-light.svg",
        dark: "./src/assets/logo-dark.svg",
        replacesTitle: true,
      },
      head: [
        {
          tag: "meta",
          attrs: {
            property: "og:image",
            content: "https://mif-spec.dev/og-image.jpg",
          },
        },
        {
          tag: "meta",
          attrs: {
            property: "og:image:width",
            content: "1280",
          },
        },
        {
          tag: "meta",
          attrs: {
            property: "og:image:height",
            content: "640",
          },
        },
        {
          tag: "meta",
          attrs: {
            name: "twitter:card",
            content: "summary_large_image",
          },
        },
        {
          tag: "meta",
          attrs: {
            name: "twitter:image",
            content: "https://mif-spec.dev/og-image.jpg",
          },
        },
      ],
      social: [
        {
          icon: "github",
          label: "GitHub",
          href: "https://github.com/modeled-information-format/MIF",
        },
      ],
      sidebar: [
        {
          label: "Overview",
          items: [{ label: "Introduction", slug: "index" }],
        },
        {
          label: "Specification",
          items: [
            {
              label: "Core",
              items: [
                { label: "Overview", slug: "specification/overview" },
                { label: "File Format", slug: "specification/file-format" },
                { label: "Data Model", slug: "specification/data-model" },
              ],
            },
            {
              label: "Formats",
              items: [
                {
                  label: "Markdown Format",
                  slug: "specification/markdown-format",
                },
                {
                  label: "JSON-LD Format",
                  slug: "specification/json-ld-format",
                },
              ],
            },
            {
              label: "Data Types",
              items: [
                { label: "Entity Types", slug: "specification/entity-types" },
                {
                  label: "Relationship Types",
                  slug: "specification/relationship-types",
                },
              ],
            },
            {
              label: "Features",
              items: [
                {
                  label: "Temporal Model",
                  slug: "specification/temporal-model",
                },
                {
                  label: "Namespace Model",
                  slug: "specification/namespace-model",
                },
                { label: "Embeddings", slug: "specification/embeddings" },
                { label: "Provenance", slug: "specification/provenance" },
              ],
            },
            {
              label: "Reference",
              items: [
                {
                  label: "Conformance Levels",
                  slug: "specification/conformance",
                },
                {
                  label: "JSON-LD Context",
                  slug: "specification/json-ld-context",
                },
                { label: "Conversion Rules", slug: "specification/conversion" },
                { label: "Security", slug: "specification/security" },
                { label: "Appendices", slug: "specification/appendices" },
              ],
            },
          ],
        },
      ],
    }),
  ],
});
