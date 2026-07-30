# =============================================================================
# 05_analise_alternativas.R
#
# ANALISE COMPLETA DE ALTERNATIVAS — varredura de alturas e combinacoes de
# reservatorios a montante de Estrela/RS.
#
# Estrutura:
#   1. Universo de alternativas (alturas x eixos x arranjo x combinacoes)
#   2. Roteamento de Puls de cada alternativa sobre o evento de referencia
#   3. Curva de frequencia e funcao de dano
#   4. Dano Esperado Anual (EAD) com e sem intervencao
#   5. Analise custo-beneficio (VPL, B/C, TIR simplificada)
#   6. Ranqueamento e fronteira de eficiencia
#
# TODOS os parametros economicos sao PRELIMINARES e estao concentrados no
# bloco PARAM. Devem ser recalibrados com o cadastro do Eixo 1.
# =============================================================================
here <- tryCatch(dirname(normalizePath(sys.frame(1)$ofile)), error = function(e) ".")
source(file.path(here, "00_config.R"))

geo <- fread(file.path(DIR_CAV, "geometria_barragens.csv"), dec = ",")
setkey(geo, barragem, altura_m)

EIXOS_K <- geo[, .(area_km2 = unique(area_controlada_km2),
                   cota_eixo = unique(cota_eixo_m)), by = barragem]
EIXOS_K[, pct_bacia := round(100 * area_km2 / BACIA$area_estrela, 1)]

cat("\n=========================================================================\n")
cat("EIXOS DISPONIVEIS\n")
cat("=========================================================================\n")
print(EIXOS_K, row.names = FALSE)
cat("\n  B1 esta a jusante de B3 + B2 (area incremental 121 km2).\n")
cat("  Combinacoes validas: B1 sozinha; B2; B3; B2+B3.  B1 nao combina com B2/B3.\n")

# =============================================================================
# PARAM — hipoteses economicas e hidrologicas (PRELIMINARES)
# =============================================================================
PARAM <- list(
  # evento de referencia
  q_pico_2024   = 18000,   # m3/s
  lamina_mm     = 260,
  q_base        = 600,
  # dano
  Q_sem_dano    = 4000,    # m3/s — limiar de dano relevante  [CALIBRAR com HEC-RAS]
  dano_2024_MRS = 2500,    # R$ milhoes — dano direto em Estrela no evento  [CALIBRAR]
  expoente_dano = 1.8,     # curvatura da funcao dano x vazao
  # frequencia
  TR_evento     = 100,     # tempo de retorno atribuido ao evento de referencia [CALIBRAR]
  cv_gumbel     = 0.45,    # coef. de variacao da serie de picos              [CALIBRAR]
  # economia
  horizonte     = 50,      # anos
  taxa_desconto = 0.06,    # 6% a.a. (padrao de projetos de infraestrutura)
  custo_OM_pct  = 0.008    # O&M anual como % do CAPEX
)

# =============================================================================
# 1. HIDROLOGIA
# =============================================================================
hidrograma <- function(qp, lam = PARAM$lamina_mm, qb = PARAM$q_base,
                       area = BACIA$area_estrela, dt_h = 1) {
  Vtot <- lam / 1000 * area * 1e6
  m <- 3.0; fV <- gamma(m + 1) * exp(m) / m^(m + 1)
  tp <- Vtot / ((qp - qb) * fV)
  t  <- seq(0, 8 * tp, by = dt_h * 3600)
  q  <- qb + (qp - qb) * (t / tp)^m * exp(m * (1 - t / tp))
  q[!is.finite(q)] <- qb
  data.table(t_h = t / 3600, Q = q)
}

# curva de frequencia Gumbel ancorada no evento de referencia
gumbel_Q <- function(TR, q_ref = PARAM$q_pico_2024, TR_ref = PARAM$TR_evento,
                     cv = PARAM$cv_gumbel) {
  # Q(TR) = mu + alpha * (-ln(-ln(1-1/TR)))
  y  <- function(T) -log(-log(1 - 1 / T))
  # mu e alpha a partir de q_ref no TR_ref e do CV
  # alpha = cv * mu * sqrt(6)/pi / (1 + 0.5772*cv*sqrt(6)/pi)  -> resolvido numericamente
  k <- cv * sqrt(6) / pi
  mu    <- q_ref / (1 + k * (y(TR_ref) - 0.5772))
  alpha <- k * mu
  mu + alpha * (y(TR) - 0.5772)
}

TRs <- c(2, 5, 10, 25, 50, 100, 200, 500, 1000)
freq <- data.table(TR = TRs, prob_exced = 1 / TRs, Q = round(gumbel_Q(TRs)))

cat("\n=========================================================================\n")
cat("CURVA DE FREQUENCIA (Gumbel ancorada no evento de referencia)\n")
cat("=========================================================================\n")
print(freq, row.names = FALSE)

# =============================================================================
# 2. FUNCAO DE DANO
# =============================================================================
#' Dano direto (R$ milhoes) em funcao da vazao de pico em Estrela
dano <- function(Q) {
  Qs <- PARAM$Q_sem_dano
  d  <- ifelse(Q <= Qs, 0,
               PARAM$dano_2024_MRS *
                 ((Q - Qs) / (PARAM$q_pico_2024 - Qs))^PARAM$expoente_dano)
  pmax(d, 0)
}

# =============================================================================
# 3. ROTEAMENTO
# =============================================================================
vertedouro     <- function(h, L, C = 2.1) ifelse(h > 0, C * L * h^1.5, 0)
descarga_fundo <- function(h, A, Cd = 0.62) ifelse(h > 0, Cd * A * sqrt(2 * 9.81 * h), 0)
A_fundo_alvo   <- function(Q, carga) Q / (0.62 * sqrt(2 * 9.81 * carga))

rotear <- function(hin, cv_dt, H_bar, H_sol, L_vert, A_fundo, dt_h = 1) {
  dt <- dt_h * 3600
  cv <- cv_dt[order(altura_m)]
  V_de_h <- approxfun(cv$altura_m, cv$volume_hm3 * 1e6, rule = 2)
  h_de_V <- approxfun(cv$volume_hm3 * 1e6, cv$altura_m, rule = 2)
  V_max  <- V_de_h(H_bar); n <- nrow(hin)
  V <- numeric(n); h <- numeric(n); Qo <- numeric(n); sat <- FALSE
  saida <- function(hh) descarga_fundo(hh, A_fundo) + vertedouro(hh - H_sol, L_vert)
  for (i in 2:n) {
    I <- (hin$Q[i - 1] + hin$Q[i]) / 2
    Vt <- V[i - 1]; Ot <- saida(h[i - 1])
    for (k in 1:20) {
      Vn <- min(max(V[i - 1] + (I - (Ot + saida(h_de_V(max(Vt, 0)))) / 2) * dt, 0), V_max)
      if (abs(Vn - Vt) < 1e3) { Vt <- Vn; break }
      Vt <- Vn
    }
    V[i] <- Vt; h[i] <- h_de_V(Vt); Qo[i] <- saida(h[i])
    if (V[i] >= V_max * 0.999) { Qo[i] <- max(Qo[i], hin$Q[i]); sat <- TRUE }
  }
  list(Qout = Qo, Vmax = max(V) / 1e6, hmax = max(h), saturou = sat)
}

#' Pico em Estrela para uma dada configuracao e um dado pico natural
pico_com_alternativa <- function(config, q_pico_nat) {
  hn <- hidrograma(q_pico_nat)
  A_ctrl <- sum(sapply(config$eixos, function(e) EIXOS_K[barragem == e, area_km2]))
  outs <- lapply(seq_along(config$eixos), function(k) {
    e  <- config$eixos[k]; H <- config$alturas[k]
    fr <- EIXOS_K[barragem == e, area_km2] / BACIA$area_estrela
    hin <- data.table(t_h = hn$t_h, Q = hn$Q * fr)
    cvb <- geo[barragem == e, .(altura_m, volume_hm3)]
    if (config$tipo == "seca") {
      Hs <- H - 4; Af <- A_fundo_alvo(PARAM$Q_sem_dano * fr / 0.81, H / 2)
    } else {
      Hs <- H * 0.75; Af <- 20 * fr / 0.81
    }
    Lv <- geo[barragem == e & altura_m == H, L_crista_m] * 0.2
    rotear(hin, cvb, H, Hs, max(Lv, 40), Af)
  })
  n <- min(sapply(outs, function(o) length(o$Qout)), nrow(hn))
  q_livre <- hn$Q[1:n] * (BACIA$area_estrela - A_ctrl) / BACIA$area_estrela
  q_tot   <- Reduce(`+`, lapply(outs, function(o) o$Qout[1:n])) + q_livre
  list(pico = max(q_tot), Vmax = sum(sapply(outs, `[[`, "Vmax")),
       saturou = any(sapply(outs, `[[`, "saturou")), A_ctrl = A_ctrl)
}

# =============================================================================
# 4. UNIVERSO DE ALTERNATIVAS
# =============================================================================
ALT_H <- seq(30, 120, by = 10)
combos <- list()
for (H in ALT_H) for (tp in c("convencional", "seca")) {
  combos[[length(combos) + 1]] <- list(id = sprintf("B1-%dm-%s", H, tp),
                                       eixos = "B1", alturas = H, tipo = tp)
  combos[[length(combos) + 1]] <- list(id = sprintf("B3-%dm-%s", H, tp),
                                       eixos = "B3", alturas = H, tipo = tp)
  combos[[length(combos) + 1]] <- list(id = sprintf("B2-%dm-%s", H, tp),
                                       eixos = "B2", alturas = H, tipo = tp)
}
# combinacoes B2+B3 (nao aninhadas entre si)
for (H3 in ALT_H) for (H2 in ALT_H) {
  combos[[length(combos) + 1]] <- list(
    id = sprintf("B3-%dm+B2-%dm-seca", H3, H2),
    eixos = c("B3", "B2"), alturas = c(H3, H2), tipo = "seca")
}
cat(sprintf("\n  %d alternativas no universo de busca.\n", length(combos)))

# =============================================================================
# 5. AVALIACAO
# =============================================================================
custo_de <- function(eixos, alturas)
  sum(sapply(seq_along(eixos), function(k)
    geo[barragem == eixos[k] & altura_m == alturas[k], custo_total_MRS]))

area_alagada_de <- function(eixos, alturas)
  sum(sapply(seq_along(eixos), function(k)
    geo[barragem == eixos[k] & altura_m == alturas[k], area_alagada_km2]))

#' EAD por integracao da funcao de dano sobre a curva de frequencia
EAD <- function(fn_pico) {
  p <- seq(0.0005, 0.5, length.out = 120)     # prob. de excedencia
  Tr <- 1 / p
  q_nat <- gumbel_Q(Tr)
  q_res <- sapply(q_nat, fn_pico)
  d <- dano(q_res)
  # EAD = INT D(Q(p)) dp, com p = probabilidade anual de excedencia (crescente)
  sum(diff(p) * (head(d, -1) + tail(d, -1)) / 2)
}

cat("  avaliando alternativas (roteamento por cenario de frequencia)...\n")
# para nao rotear 120 vazoes por alternativa, usa-se uma malha de 7 vazoes
# e interpolacao da relacao Q_natural -> Q_resultante
Q_MALHA <- gumbel_Q(c(2, 5, 10, 25, 50, 100, 250, 500, 1000))

aval <- rbindlist(lapply(combos, function(cf) {
  picos <- sapply(Q_MALHA, function(q) pico_com_alternativa(cf, q)$pico)
  f_int <- approxfun(Q_MALHA, picos, rule = 2)
  r2024 <- pico_com_alternativa(cf, PARAM$q_pico_2024)
  cst   <- custo_de(cf$eixos, cf$alturas)
  ead0  <- EAD(function(q) q)
  ead1  <- EAD(f_int)
  benef_anual <- ead0 - ead1
  fa <- (1 - (1 + PARAM$taxa_desconto)^(-PARAM$horizonte)) / PARAM$taxa_desconto
  vpl_benef <- benef_anual * fa
  vpl_custo <- cst * (1 + PARAM$custo_OM_pct * fa)
  data.table(
    alternativa = cf$id, eixos = paste(cf$eixos, collapse = "+"),
    alturas = paste(cf$alturas, collapse = "/"), arranjo = cf$tipo,
    area_ctrl_km2 = round(r2024$A_ctrl),
    pct_bacia = round(100 * r2024$A_ctrl / BACIA$area_estrela, 1),
    V_util_hm3 = round(r2024$Vmax),
    area_alagada_km2 = round(area_alagada_de(cf$eixos, cf$alturas), 1),
    pico_2024_com = round(r2024$pico),
    reducao_pct = round(100 * (1 - r2024$pico / PARAM$q_pico_2024), 1),
    saturou = r2024$saturou,
    custo_MRS = round(cst),
    EAD_sem_MRS = round(ead0, 1), EAD_com_MRS = round(ead1, 1),
    benef_anual_MRS = round(benef_anual, 1),
    VPL_benef_MRS = round(vpl_benef), VPL_custo_MRS = round(vpl_custo),
    VPL_liq_MRS = round(vpl_benef - vpl_custo),
    BC = round(vpl_benef / vpl_custo, 2))
}))

setorder(aval, -BC)
fwrite(aval, file.path(DIR_TAB, "analise_alternativas_completa.csv"), sep = ";", dec = ",")

cat("\n=========================================================================\n")
cat("TOP 15 ALTERNATIVAS POR RAZAO BENEFICIO-CUSTO\n")
cat("=========================================================================\n")
print(aval[1:15, .(alternativa, arranjo, V_util_hm3, area_alagada_km2,
                   pico_2024_com, reducao_pct, custo_MRS, VPL_liq_MRS, BC)],
      row.names = FALSE)

cat("\n=========================================================================\n")
cat("MELHOR ALTERNATIVA POR FAIXA DE REDUCAO DE PICO\n")
cat("=========================================================================\n")
aval[, faixa := cut(reducao_pct, c(-Inf, 10, 20, 30, 40, 50, 60, Inf),
                    labels = c("<10%", "10-20%", "20-30%", "30-40%",
                               "40-50%", "50-60%", ">60%"))]
melhores <- aval[order(-BC), .SD[1], by = faixa][order(faixa)]
print(melhores[, .(faixa, alternativa, arranjo, V_util_hm3, area_alagada_km2,
                   reducao_pct, custo_MRS, BC)], row.names = FALSE)

cat("\n=========================================================================\n")
cat("ALTERNATIVAS ECONOMICAMENTE VIAVEIS (B/C > 1)\n")
cat("=========================================================================\n")
viaveis <- aval[BC > 1]
if (nrow(viaveis) == 0) {
  cat("  NENHUMA alternativa apresenta B/C > 1 sob as hipoteses adotadas.\n")
  cat(sprintf("  Melhor B/C obtido: %.2f (%s)\n", aval$BC[1], aval$alternativa[1]))
} else {
  print(viaveis[1:min(10, nrow(viaveis)),
                .(alternativa, arranjo, reducao_pct, custo_MRS, VPL_liq_MRS, BC)],
        row.names = FALSE)
}
fwrite(melhores, file.path(DIR_TAB, "melhores_por_faixa_reducao.csv"), sep = ";", dec = ",")

# =============================================================================
# 6. FIGURAS
# =============================================================================
g1 <- ggplot(aval, aes(custo_MRS, reducao_pct, colour = arranjo, shape = eixos)) +
  geom_point(alpha = .75, size = 2) +
  scale_x_continuous(labels = label_number(big.mark = ".", decimal.mark = ",")) +
  labs(title = "Fronteira custo x eficácia das alternativas de reservatório",
       subtitle = "redução do pico do evento de referência em Estrela",
       x = "custo de implantação (R$ milhões)", y = "redução do pico (%)",
       colour = "arranjo", shape = "eixos") +
  tema_sedec()

g2 <- ggplot(aval, aes(V_util_hm3, reducao_pct, colour = arranjo)) +
  geom_point(alpha = .7, size = 2) +
  labs(title = "Volume de amortecimento efetivamente utilizado x redução do pico",
       x = "volume utilizado no evento (hm³)", y = "redução do pico (%)", colour = NULL) +
  tema_sedec()

g3 <- ggplot(aval, aes(area_alagada_km2, reducao_pct, colour = eixos)) +
  geom_point(alpha = .7, size = 2) +
  labs(title = "Área inundada pelo reservatório x redução do pico",
       subtitle = "medida do custo socioambiental de cada alternativa",
       x = "área alagada (km²)", y = "redução do pico (%)", colour = NULL) +
  tema_sedec()

ggsave(file.path(DIR_FIG, "06_fronteira_custo_eficacia.png"), g1, width = 9.5, height = 5.5, dpi = 160)
ggsave(file.path(DIR_FIG, "07_volume_x_reducao.png"),        g2, width = 9, height = 5, dpi = 160)
ggsave(file.path(DIR_FIG, "08_area_alagada_x_reducao.png"),  g3, width = 9, height = 5, dpi = 160)

cat("\n  tabelas e figuras 06-08 gravadas em ", DIR_OUT, "\n", sep = "")
