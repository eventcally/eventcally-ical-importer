import { describe, expect, it } from "vitest";
import { createI18n } from "vue-i18n";
import de from "@/locales/de.json";
import en from "@/locales/en.json";

// The msgids are the keys, also when they contain dots, question marks or placeholders.
const i18n = (locale: string) =>
  createI18n({ legacy: false, locale, fallbackLocale: "en", messages: { de, en } }).global;

describe("locale messages", () => {
  it("translates msgids with punctuation to German", () => {
    const { t } = i18n("de");

    expect(t("Loading...")).toBe("Lädt...");
    expect(t("Delete configuration?")).toBe("Konfiguration löschen?");
    expect(t("Create a configuration for one of your organizations.")).toBe(
      "Erstelle eine Konfiguration für eine deiner Organisationen.",
    );
    expect(t("Update %(title)s", { title: "Sitzungen" })).toBe("Sitzungen bearbeiten");
  });

  it("falls back to the English msgid", () => {
    const { t } = i18n("en");

    expect(t("Loading...")).toBe("Loading...");
    expect(t("Update %(title)s", { title: "Sitzungen" })).toBe("Update Sitzungen");
  });
});
