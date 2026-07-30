# =============================================================================
# 07_comportas_uso_multiplo.R
#
# BARRAGEM DE USO MULTIPLO — vertedouro com comportas + geracao hidreletrica.
#
# O resultado central das analises anteriores foi que apenas a barragem SECA
# amortece de forma relevante, porque o vertedouro de soleira LIVRE perde o
# controle assim que o NA supera a soleira. Isso, porem, e' incompativel com
# geracao de energia, que exige reservatorio cheio.
#
# O VERTEDOURO COM COMPORTAS resolve o conflito: permite manter um NA maximo
# NORMAL alto (energia) e, ao mesmo tempo, (i) deplecionar preventivamente o
# reservatorio na iminencia da cheia, abrindo o VOLUME DE ESPERA, e
# (ii) limitar a descarga durante o evento ate a capacidade das comportas.
#
# Este script quantifica o trade-off:
#     NA normal alto  -> mais energia, menos volume de espera, menos protecao
#     NA normal baixo -> mais protecao, menos energia
#
# Nomenclatura (ABNT / Eletrobras — inventario hidreletrico):
#   NA max normal      : nivel de operacao normal (topo do volume util)
#   Volume de espera   : entre NA max normal e NA max maximorum
#   NA max maximorum   : nivel maximo durante a cheia de projeto
#   Crista             : NA max maximorum + borda livre
# =============================================================================
here <- tryCatch(dirname(normalizePath(sys.frame(1)$ofile)), error = function(e) ".")
source(file.path(here, "00_config.R"))

geo <- fread(file.path(DIR_CAV, "geometria_todos.csv"), dec = ",")
eix <- fread(file.path(DIR_CAV, "eixos_todos.csv"), dec = ",")
setkey(geo, eixo, altura_m)

# =============================================================================
# PARAMETROS
# =============================================================================
PAR <- list(
  q_pico_2024 = 18000, lamina_mm = 260, q_base = 600, dt_h = 1,
  Q_sem_dano  = 4000,
  # ---- comportas ----
  Cd_comporta = 0.61,      # coef. de descarga (comporta segmento, orificio)
  # ---- geracao ----
  rendimento  = 0.90,      # turbina + gerador
  perda_carga = 0.03,      # perda no circuito de aducao (fracao da queda bruta)
  fator_capac = 0.55,      # fator de capacidade tipico
  tarifa_MWh  = 250,       # R$/MWh
  # ---- operacao ----
  antecedencia_h = 48,     # antecedencia da previsao para deplecionamento
  # ---- economia ----
  horizonte = 50, taxa = 0.06, om_pct = 0.008,
  dano_2024_MRS = 2500, TR_evento = 100, cv_gumbel = 0.45, expoente_dano = 1.8
)

EIXO_ALVO <- "E12"          # eixo mais a jusante (15.760 km2, 81% da bacia)
AREA_CTRL <- eix[codigo == EIXO_ALVO, area_km2]
COTA_EIXO <- eix[codigo == EIXO_ALVO, cota_eixo_m]

cat("\n=========================================================================\n")
cat(sprintf("EIXO ANALISADO: %s | area %s km2 (%.1f%% da bacia) | cota %.1f m\n",
            EIXO_ALVO, format(AREA_CTRL, big.mark = ".", decimal.mark = ","),
            100 * AREA_CTRL / BACIA$area_estrela, COTA_EIXO))
cat("=========================================================================\n")

# =============================================================================
# HIDROLOGIA
# =============================================================================
hidrograma <- function(qp, area = BACIA$area_estrela) {
  Vt <- PAR$lamina_mm / 1000 * area * 1e6
  m <- 3.0; fV <- gamma(m + 1) * exp(m) / m^(m + 1)
  qb <- PAR$q_base * area / BACIA$area_estrela
  tp <- Vt / ((qp - qb) * fV)
  t  <- seq(0, 10 * tp, by = PAR$dt_h * 3600)
  q  <- qb + (qp - qb) * (t / tp)^m * exp(m * (1 - t / tp))
  q[!is.finite(q)] <- qb
  data.table(t_h = t / 3600, Q = q)
}
gumbel_Q <- function(TR, qref = PAR$q_pico_2024, TRref = PAR$TR_evento, cv = PAR$cv_gumbel) {
  y <- function(T) -log(-log(1 - 1 / T))
  k <- cv * sqrt(6) / pi
  mu <- qref / (1 + k * (y(TRref) - 0.5772))
  mu + k * mu * (y(TR) - 0.5772)
}
dano <- function(Q) pmax(0, ifelse(Q <= PAR$Q_sem_dano, 0,
  PAR$dano_2024_MRS * ((Q - PAR$Q_sem_dano) / (PAR$q_pico_2024 - PAR$Q_sem_dano))^PAR$expoente_dano))

# =============================================================================
# ESTRUTURAS DE DESCARGA
# =============================================================================
#' Vertedouro com comportas: descarga controlada ate a capacidade maxima.
#' Com as comportas totalmente abertas comporta-se como soleira livre.
#' @param h      carga sobre o eixo (m)
#' @param h_sol  cota da soleira acima do eixo (m)
#' @param L      comprimento total da soleira (m)
#' @param abert  fracao de abertura (0 a 1)
vert_comporta <- function(h, h_sol, L, abert = 1, C = 2.1) {
  carga <- pmax(h - h_sol, 0)
  q_livre <- C * L * carga^1.5
  q_livre * pmin(pmax(abert, 0), 1)
}
descarga_fundo <- function(h, A, Cd = PAR$Cd_comporta)
  ifelse(h > 0, Cd * A * sqrt(2 * 9.81 * h), 0)

# =============================================================================
# ROTEAMENTO COM OPERACAO POR REGRA
# =============================================================================
#' @param H_bar    altura da barragem (m acima do eixo)
#' @param H_normal cota do NA maximo normal (m acima do eixo)
#' @param L_sol    comprimento da soleira do vertedouro (m)
#' @param A_fundo  area da descarga de fundo (m2)
#' @param Q_meta   descarga-alvo durante o evento (m3/s)
#' @param deplec   TRUE = deplecionamento preventivo ate o NA normal - dh
#' @param dh_prev  rebaixamento preventivo (m)
rotear_comportas <- function(hin, cv, H_bar, H_normal, L_sol, A_fundo,
                             Q_meta, deplec = TRUE, dh_prev = 0) {
  dt <- PAR$dt_h * 3600
  cv <- cv[order(altura_m)]
  V_de_h <- approxfun(cv$altura_m, cv$volume_hm3 * 1e6, rule = 2)
  h_de_V <- approxfun(cv$volume_hm3 * 1e6, cv$altura_m, rule = 2)
  V_max  <- V_de_h(H_bar)
  V_norm <- V_de_h(H_normal)
  V_ini  <- if (deplec) V_de_h(max(H_normal - dh_prev, 0)) else V_norm
  V_espera <- V_max - V_ini

  n <- nrow(hin)
  V <- numeric(n); h <- numeric(n); Qo <- numeric(n); ab <- numeric(n)
  V[1] <- V_ini; h[1] <- h_de_V(V_ini)
  sat <- FALSE; galga <- FALSE

  for (i in 2:n) {
    I  <- (hin$Q[i - 1] + hin$Q[i]) / 2
    Vp <- V[i - 1]; hp <- h[i - 1]

    # capacidade maxima de descarga na carga atual
    q_cap <- vert_comporta(hp, H_normal, L_sol, 1) + descarga_fundo(hp, A_fundo)

    if (Vp >= V_max * 0.995) {
      # Reservatorio cheio: as comportas modulam para passar exatamente a
      # afluencia (regime permanente). Verter MAIS que a afluencia esvaziaria
      # o reservatorio e nao e' o que ocorre no pico. Se nem com as comportas
      # totalmente abertas a capacidade alcanca a afluencia, ha galgamento.
      Qt <- min(q_cap, I); sat <- TRUE
      if (q_cap < I) galga <- TRUE
      abert <- 1
    } else {
      # regra de operacao: liberar o minimo entre a meta e a capacidade
      Qt <- min(Q_meta, q_cap)
      # se o volume de espera esta acabando, antecipa a abertura
      ocup <- (Vp - V_ini) / max(V_max - V_ini, 1)
      if (ocup > 0.85) Qt <- min(q_cap, max(Q_meta, I * (ocup - 0.85) / 0.15))
      abert <- if (q_cap > 0) min(Qt / q_cap, 1) else 0
    }
    Vn <- Vp + (I - Qt) * dt
    if (Vn > V_max) {
      # Reservatorio cheio: nao ha mais volume para amortecer, de modo que o
      # efluente iguala o afluente (regime permanente). Nao ha "pico" de saida:
      # uma barragem cheia TRANSFERE a cheia, nao a amplifica.
      Qt <- max(Qt, I)
      Vn <- min(Vp + (I - Qt) * dt, V_max)
      sat <- TRUE
      # se nem as comportas totalmente abertas dao conta, ha galgamento
      if (q_cap < I) galga <- TRUE
    }
    if (Vn < 0)     { Qt <- max(Qt + Vn / dt, 0);  Vn <- 0 }
    V[i] <- Vn; h[i] <- h_de_V(Vn); Qo[i] <- Qt; ab[i] <- abert
  }
  list(t_h = hin$t_h, Qin = hin$Q, Qout = Qo, V_hm3 = V / 1e6, h_m = h,
       abertura = ab, saturou = sat, galgou = galga, V_espera_hm3 = V_espera / 1e6,
       V_util_hm3 = V_norm / 1e6, h_max = max(h))
}

# =============================================================================
# GERACAO DE ENERGIA
# =============================================================================
#' Energia media anual (GWh) para um dado NA normal
#' Queda bruta = NA normal - nivel de jusante (aproximado pela cota do eixo)
energia_anual <- function(H_normal, q_medio_m3s, q_engolimento) {
  H_bruta <- H_normal                        # eixo = nivel de restituicao
  H_liq   <- H_bruta * (1 - PAR$perda_carga)
  Q_turb  <- min(q_medio_m3s, q_engolimento)
  P_MW    <- 9.81 * Q_turb * H_liq * PAR$rendimento / 1000
  list(P_instalada_MW = round(9.81 * q_engolimento * H_liq * PAR$rendimento / 1000, 1),
       P_media_MW = round(P_MW, 1),
       E_anual_GWh = round(P_MW * 8760 / 1000, 1),
       H_liquida_m = round(H_liq, 1))
}

# vazao media de longo termo na secao (estimativa por rendimento especifico)
Q_ESPECIFICO <- 0.020            # m3/s/km2 — Taquari-Antas  [CALIBRAR com ANA]
Q_MEDIA <- AREA_CTRL * Q_ESPECIFICO
cat(sprintf("\n  Vazao media de longo termo estimada: %.0f m3/s (%.3f m3/s/km2)\n",
            Q_MEDIA, Q_ESPECIFICO))
cat("  [CALIBRAR com a serie da ANA — parametro sensivel para a energia]\n")

# =============================================================================
# VARREDURA: altura da barragem x NA normal
# =============================================================================
ALTURAS <- c(60, 70, 80, 90, 100, 110, 120)
FRAC_NORMAL <- c(0.30, 0.45, 0.60, 0.70, 0.80, 0.90)   # NA normal / altura

cat("\n=========================================================================\n")
cat("VARREDURA — ALTURA x NA MAXIMO NORMAL (uso multiplo com comportas)\n")
cat("=========================================================================\n")

fa <- (1 - (1 + PAR$taxa)^(-PAR$horizonte)) / PAR$taxa
Q_MALHA <- gumbel_Q(c(2, 5, 10, 25, 50, 100, 250, 500, 1000))

res <- rbindlist(lapply(ALTURAS, function(H) {
  g <- geo[eixo == EIXO_ALVO & altura_m == H]
  if (!nrow(g)) return(NULL)
  cv <- geo[eixo == EIXO_ALVO, .(altura_m, volume_hm3)]
  # Vertedouro dimensionado para descarregar a cheia de projeto (TR 10.000
  # anos) com a sobrelevacao disponivel acima do NA normal. E o criterio
  # de projeto usual; um vertedouro arbitrariamente longo produziria
  # descargas fisicamente impossiveis.
  Q_projeto <- gumbel_Q(10000) * AREA_CTRL / BACIA$area_estrela
  A_fundo <- 30
  rbindlist(lapply(FRAC_NORMAL, function(fr) {
    Hn <- H * fr
    sobrelev <- max(H - Hn, 2)                 # carga maxima sobre a soleira
    L_sol <- min(max(Q_projeto / (2.1 * sobrelev^1.5), 40),
                 g$L_crista_m * 0.5)           # limitado a 50% da crista
    # picos resultantes para a malha de frequencia
    picos <- sapply(Q_MALHA, function(qp) {
      hn <- hidrograma(qp, AREA_CTRL)
      r  <- rotear_comportas(hn, cv, H, Hn, L_sol, A_fundo,
                             Q_meta = PAR$Q_sem_dano * AREA_CTRL / BACIA$area_estrela,
                             deplec = TRUE, dh_prev = min(5, Hn * 0.15))
      q_livre <- qp * (BACIA$area_estrela - AREA_CTRL) / BACIA$area_estrela
      max(r$Qout) + q_livre
    })
    f_int <- approxfun(Q_MALHA, picos, rule = 2)
    hn24 <- hidrograma(PAR$q_pico_2024, AREA_CTRL)
    r24 <- rotear_comportas(hn24, cv, H, Hn, L_sol, A_fundo,
                            Q_meta = PAR$Q_sem_dano * AREA_CTRL / BACIA$area_estrela,
                            deplec = TRUE, dh_prev = min(5, Hn * 0.15))
    pico24 <- max(r24$Qout) + PAR$q_pico_2024 * (BACIA$area_estrela - AREA_CTRL) / BACIA$area_estrela

    # energia
    q_eng <- Q_MEDIA * 2.2                       # engolimento ~ 2,2 x Qmlt
    en <- energia_anual(Hn, Q_MEDIA * PAR$fator_capac / 0.55, q_eng)
    receita <- en$E_anual_GWh * 1000 * PAR$tarifa_MWh / 1e6   # R$ milhoes/ano

    # EAD
    p <- seq(0.0005, 0.5, length.out = 100)
    ead0 <- sum(diff(p) * (head(dano(gumbel_Q(1/p)), -1) + tail(dano(gumbel_Q(1/p)), -1)) / 2)
    dcom <- dano(f_int(gumbel_Q(1/p)))
    ead1 <- sum(diff(p) * (head(dcom, -1) + tail(dcom, -1)) / 2)

    custo <- g$custo_total_MRS * 1.25            # +25% casa de forca/turbinas
    vpl_b <- (ead0 - ead1 + receita) * fa
    vpl_c <- custo * (1 + PAR$om_pct * fa)

    data.table(altura_m = H, frac_NA = fr, NA_normal_m = round(Hn, 1),
               cota_NA_normal = round(COTA_EIXO + Hn, 1),
               cota_crista = g$cota_crista_m,
               V_util_hm3 = round(r24$V_util_hm3),
               V_espera_hm3 = round(r24$V_espera_hm3),
               area_alagada_km2 = g$area_alagada_km2,
               pico_2024 = round(pico24),
               reducao_pct = round(100 * (1 - pico24 / PAR$q_pico_2024), 1),
               saturou = r24$saturou,
               P_MW = en$P_instalada_MW, E_GWh = en$E_anual_GWh,
               receita_MRS_ano = round(receita, 1),
               benef_dano_MRS_ano = round(ead0 - ead1, 1),
               custo_MRS = round(custo),
               VPL_liq_MRS = round(vpl_b - vpl_c),
               BC = round(vpl_b / vpl_c, 2))
  }))
}))

print(res[, .(altura_m, NA_normal_m, V_util_hm3, V_espera_hm3, area_alagada_km2,
              pico_2024, reducao_pct, P_MW, E_GWh, receita_MRS_ano,
              benef_dano_MRS_ano, custo_MRS, VPL_liq_MRS, BC)], row.names = FALSE)

fwrite(res, file.path(DIR_TAB, "uso_multiplo_comportas.csv"), sep = ";", dec = ",")

cat("\n=========================================================================\n")
cat("MELHORES ARRANJOS POR CRITERIO\n")
cat("=========================================================================\n")
cat("\n-- maior VPL liquido --\n")
print(res[order(-VPL_liq_MRS)][1:5, .(altura_m, NA_normal_m, reducao_pct, E_GWh,
                                      custo_MRS, VPL_liq_MRS, BC)], row.names = FALSE)
cat("\n-- maior reducao de pico --\n")
print(res[order(-reducao_pct)][1:5, .(altura_m, NA_normal_m, reducao_pct, E_GWh,
                                      custo_MRS, VPL_liq_MRS, BC)], row.names = FALSE)
cat("\n-- maior energia --\n")
print(res[order(-E_GWh)][1:5, .(altura_m, NA_normal_m, reducao_pct, E_GWh,
                                custo_MRS, VPL_liq_MRS, BC)], row.names = FALSE)

# =============================================================================
# FIGURAS
# =============================================================================
g1 <- ggplot(res, aes(E_GWh, reducao_pct, colour = factor(altura_m))) +
  geom_point(size = 2.4) + geom_line(aes(group = altura_m), alpha = .5) +
  labs(title = "Trade-off energia x proteção contra cheias",
       subtitle = "cada linha é uma altura de barragem; cada ponto, um NA máximo normal",
       x = "energia média anual (GWh)", y = "redução do pico do evento (%)",
       colour = "altura (m)") +
  tema_sedec()

g2 <- ggplot(res, aes(V_espera_hm3, reducao_pct, colour = factor(altura_m))) +
  geom_point(size = 2.4) + geom_line(aes(group = altura_m), alpha = .5) +
  labs(title = "Volume de espera x redução do pico",
       x = "volume de espera (hm³)", y = "redução do pico (%)", colour = "altura (m)") +
  tema_sedec()

g3 <- ggplot(res, aes(custo_MRS, VPL_liq_MRS, colour = factor(altura_m),
                      size = reducao_pct)) +
  geom_point(alpha = .8) +
  geom_hline(yintercept = 0, linetype = "dashed", colour = "grey40") +
  scale_x_continuous(labels = label_number(big.mark = ".", decimal.mark = ",")) +
  scale_y_continuous(labels = label_number(big.mark = ".", decimal.mark = ",")) +
  labs(title = "Viabilidade dos arranjos de uso múltiplo",
       subtitle = "benefício = dano evitado + receita de energia",
       x = "custo de implantação (R$ milhões)", y = "VPL líquido (R$ milhões)",
       colour = "altura (m)", size = "redução (%)") +
  tema_sedec()

ggsave(file.path(DIR_FIG, "10_tradeoff_energia_protecao.png"), g1, width = 9.5, height = 5.5, dpi = 160)
ggsave(file.path(DIR_FIG, "11_volume_espera_reducao.png"),     g2, width = 9, height = 5, dpi = 160)
ggsave(file.path(DIR_FIG, "12_viabilidade_uso_multiplo.png"),  g3, width = 9.5, height = 5.5, dpi = 160)

# ------------------------------- hidrograma detalhado do melhor arranjo
best <- res[order(-VPL_liq_MRS)][1]
cv <- geo[eixo == EIXO_ALVO, .(altura_m, volume_hm3)]
gg <- geo[eixo == EIXO_ALVO & altura_m == best$altura_m]
hn <- hidrograma(PAR$q_pico_2024, AREA_CTRL)
rr <- rotear_comportas(hn, cv, best$altura_m, best$NA_normal_m,
                       max(gg$L_crista_m * .25, 60), 30,
                       Q_meta = PAR$Q_sem_dano * AREA_CTRL / BACIA$area_estrela,
                       deplec = TRUE, dh_prev = min(5, best$NA_normal_m * .15))
q_livre <- hn$Q * (BACIA$area_estrela - AREA_CTRL) / BACIA$area_estrela
det <- data.table(t_h = rr$t_h,
                  `Natural em Estrela` = hn$Q + q_livre,
                  `Afluente ao reservatório` = rr$Qin,
                  `Efluente (comportas)` = rr$Qout,
                  `Resultante em Estrela` = rr$Qout + q_livre)
pl <- melt(det, id.vars = "t_h", variable.name = "serie", value.name = "Q")
g4 <- ggplot(pl, aes(t_h, Q, colour = serie)) +
  geom_line(linewidth = .9) +
  geom_hline(yintercept = PAR$Q_sem_dano, linetype = "dashed", colour = "grey35") +
  annotate("text", x = max(det$t_h) * .8, y = PAR$Q_sem_dano * 1.15,
           label = "vazão sem dano relevante", size = 3.2, colour = "grey30") +
  scale_y_continuous(labels = label_number(big.mark = ".", decimal.mark = ",")) +
  scale_colour_manual(values = c("#8b1f2e", "#c26a2a", "#1f5c8b", "#2e8b7a")) +
  labs(title = sprintf("Operação com comportas — %s, %d m, NA normal %.0f m",
                       EIXO_ALVO, best$altura_m, best$NA_normal_m),
       subtitle = sprintf("volume de espera %d hm³ | redução do pico %.1f%% | %.0f GWh/ano",
                          best$V_espera_hm3, best$reducao_pct, best$E_GWh),
       x = "tempo (h)", y = expression(vaz*ã*o~(m^3/s)), colour = NULL) +
  tema_sedec()
ggsave(file.path(DIR_FIG, "13_operacao_comportas.png"), g4, width = 9.5, height = 5.5, dpi = 160)

fwrite(det, file.path(DIR_TAB, "hidrogramas_operacao_comportas.csv"), sep = ";", dec = ",")
cat("\n  figuras 10-13 e tabelas gravadas.\n")
