# =============================================================================
# EUROCLIMA+ / AECID — Estudo integrado Estrela-RS (Taquari-Antas)
# 00_config.R — parametros gerais do estudo de alternativas de barragens
#
# Cassio Rampinelli — SEDEC/MIDR
# =============================================================================

suppressPackageStartupMessages({
  library(data.table); library(ggplot2); library(dplyr); library(tidyr)
  library(scales);     library(patchwork)
})

# ------------------------------------------------------------------ diretorios
RAIZ <- normalizePath(file.path(dirname(sys.frame(1)$ofile %||% "."), ".."),
                      mustWork = FALSE)
if (!dir.exists(RAIZ) || !dir.exists(file.path(RAIZ, "01_dados")))
  RAIZ <- "C:/Users/cassi/OneDrive/Documents/SEDEC/PROJETO_EUROCLIMA/05_MODELAGEM"

DIR_DADOS <- file.path(RAIZ, "01_dados")
DIR_CAV   <- file.path(DIR_DADOS, "cav")
DIR_ANA   <- file.path(DIR_DADOS, "ana_hidroweb")
DIR_OUT   <- file.path(RAIZ, "06_resultados")
DIR_FIG   <- file.path(DIR_OUT, "figuras")
DIR_TAB   <- file.path(DIR_OUT, "tabelas")
for (d in c(DIR_OUT, DIR_FIG, DIR_TAB, DIR_ANA)) dir.create(d, showWarnings = FALSE, recursive = TRUE)

# --------------------------------------------------------- bacia e referencias
BACIA <- list(
  nome            = "Taquari-Antas",
  area_estrela    = 19440,   # km2 — area de drenagem no inicio do trecho modelado
  area_taquari    = 23618,   # km2 — bacia total (exutorio Taquari)
  municipio       = "Estrela/RS"
)

# Postos fluviometricos ANA/CPRM de interesse (HidroWeb)
POSTOS <- data.table(
  codigo = c(86870000, 86879300, 86510000, 86720000, 86560000, 86440000),
  nome   = c("Lajeado (antigo)", "Estrela / Lajeado (atual)", "Muçum",
             "Encantado", "Passo Tainhas / Antas", "Bento Gonçalves"),
  papel  = c("historico", "referencia_estrela", "montante_principal",
             "montante", "cabeceira", "cabeceira"),
  area_km2 = c(NA, NA, NA, NA, NA, NA)
)

# ------------------------------------------------------ eixos de barragem (D8)
# Resultado da delineacao sobre Fdr.tif (28,6 m) — ver 07_python/02_bacias_barragens.py
EIXOS <- data.table(
  id          = c("BAR-A", "BAR-A2", "BAR-B"),
  descricao   = c("Taquari — jusante da confluencia (controla 81% da bacia)",
                  "Rio das Antas/Taquari — ramo principal",
                  "Tributario — ramo secundario"),
  lat         = c(-29.16163, -29.08147, -29.05970),
  lon         = c(-51.83560, -51.65664, -51.71858),
  area_km2    = c(15759.6, 12777.4, 2549.3),
  cota_eixo_m = c(47.0, 72.0, 72.0)
)
# BAR-A e' a JUSANTE de BAR-A2 + BAR-B (bacias aninhadas!)
# area incremental A = 15759.6 - 12777.4 - 2549.3 = 432.9 km2
EIXOS[, aninhado_em := c(NA, "BAR-A", "BAR-A")]

# ------------------------------------------------------- limiares de dano/dano
# Cotas de referencia do rio Taquari em Estrela/Lajeado (regua 86879300, m)
COTAS <- list(
  atencao      = 17.0,   # inicio de extravasamento em areas baixas
  alerta       = 19.0,
  inundacao    = 21.0,   # inundacao urbana significativa
  cheia_1941   = 29.92,  # marca historica ate 2023 (serie consistida UFRGS)
  cheia_2023_09 = 30.20, # setembro/2023 — superou 1941
  cheia_2024_05 = 30.50  # maio/2024 — PREENCHER com valor consistido
)

# Vazao "segura" em Estrela — abaixo da qual nao ha dano relevante.
# PARAMETRO-CHAVE do estudo: deve ser calibrado com a modelagem hidraulica 2D.
Q_SEGURA <- 4000   # m3/s  (valor preliminar — REVISAR com HEC-RAS)

# ------------------------------------------------------------------- graficos
tema_sedec <- function(base = 11) {
  theme_minimal(base_size = base) +
    theme(panel.grid.minor = element_blank(),
          plot.title    = element_text(face = "bold"),
          plot.subtitle = element_text(colour = "grey35"),
          plot.caption  = element_text(colour = "grey45", size = base - 2),
          legend.position = "bottom")
}
PAL <- c("BAR-A" = "#1f5c8b", "BAR-A2" = "#2e8b7a", "BAR-B" = "#c26a2a",
         "Sem barragem" = "#8b1f2e", "Observado" = "#333333")

`%||%` <- function(a, b) if (is.null(a)) b else a

message("config carregada — raiz: ", RAIZ)
