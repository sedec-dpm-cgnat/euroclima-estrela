# =============================================================================
# 03_roteamento_puls.R
#
# Roteamento de reservatorio (metodo de Puls / piscina nivelada) para verificar
# o amortecimento efetivo dos eixos candidatos sobre o evento de referencia.
#
# Diferenca em relacao ao 02_: aqui NAO se assume retencao perfeita. O
# reservatorio verte assim que o NA supera a soleira, e a descarga de fundo
# opera continuamente. E' o teste realista da hipotese "barragens resolvem".
# =============================================================================
here <- tryCatch(dirname(normalizePath(sys.frame(1)$ofile)), error = function(e) ".")
source(file.path(here, "00_config.R"))

cav <- fread(file.path(DIR_CAV, "cav_barragens.csv"), dec = ",")
setnames(cav, c("barragem", "altura_m", "cota_NA_m", "area_km2", "volume_hm3"))

# ------------------------------------------------------------ evento de entrada
PAR_EVENTO <- list(area_km2 = BACIA$area_estrela, q_pico = 18000,
                   q_base = 600, lamina_mm = 260, dt_h = 1)

hidrograma_gama <- function(p, area_km2 = p$area_km2) {
  esc  <- area_km2 / p$area_km2                        # escala por area de drenagem
  Vtot <- p$lamina_mm / 1000 * area_km2 * 1e6
  qp   <- p$q_pico * esc^0.85                          # atenuacao geomorfologica
  qb   <- p$q_base * esc
  m <- 3.0; fV <- gamma(m + 1) * exp(m) / m^(m + 1)
  tp <- Vtot / ((qp - qb) * fV)
  t  <- seq(0, 8 * tp, by = p$dt_h * 3600)
  q  <- qb + (qp - qb) * (t / tp)^m * exp(m * (1 - t / tp))
  q[!is.finite(q)] <- qb
  data.table(t_h = t / 3600, Q = q)
}

# =============================================================================
# Estruturas de descarga
# =============================================================================
#' Vertedouro de soleira livre:  Q = C * L * H^(3/2)
vertedouro <- function(h_sobre_soleira, L, C = 2.1) {
  ifelse(h_sobre_soleira > 0, C * L * h_sobre_soleira^1.5, 0)
}
#' Descarga de fundo (orificio afogado): Q = Cd * A * sqrt(2 g h)
descarga_fundo <- function(carga, A, Cd = 0.62) {
  ifelse(carga > 0, Cd * A * sqrt(2 * 9.81 * carga), 0)
}

# =============================================================================
# Roteamento de Puls
# =============================================================================
#' @param hin      data.table(t_h, Q) — hidrograma afluente
#' @param cav_b    curva cota-area-volume do eixo (altura_m, volume_hm3)
#' @param H_bar    altura da barragem (m)
#' @param H_sol    altura da soleira do vertedouro acima do eixo (m)
#' @param L_vert   comprimento do vertedouro (m)
#' @param A_fundo  area da descarga de fundo (m2); 0 = fechada
rotear_puls <- function(hin, cav_b, H_bar, H_sol, L_vert, A_fundo = 0, dt_h = 1) {
  dt <- dt_h * 3600
  cv <- cav_b[order(altura_m)]
  V_de_h <- approxfun(cv$altura_m, cv$volume_hm3 * 1e6, rule = 2)   # m3
  h_de_V <- approxfun(cv$volume_hm3 * 1e6, cv$altura_m, rule = 2)
  V_max  <- V_de_h(H_bar)

  n <- nrow(hin)
  V <- numeric(n); h <- numeric(n); Qout <- numeric(n); vertendo <- logical(n)
  V[1] <- 0; h[1] <- 0

  saida <- function(hh) {
    descarga_fundo(hh, A_fundo) + vertedouro(hh - H_sol, L_vert)
  }

  for (i in 2:n) {
    I  <- (hin$Q[i - 1] + hin$Q[i]) / 2
    # iteracao implicita simples (Puls)
    Vt <- V[i - 1]; Ot <- saida(h[i - 1])
    for (k in 1:25) {
      Vn <- V[i - 1] + (I - (Ot + saida(h_de_V(max(Vt, 0)))) / 2) * dt
      Vn <- min(max(Vn, 0), V_max)
      if (abs(Vn - Vt) < 1e3) { Vt <- Vn; break }
      Vt <- Vn
    }
    V[i] <- Vt; h[i] <- h_de_V(Vt)
    Qout[i] <- saida(h[i])
    if (V[i] >= V_max * 0.999) {          # reservatorio cheio: passa tudo
      Qout[i] <- max(Qout[i], hin$Q[i])
      vertendo[i] <- TRUE
    }
  }
  data.table(t_h = hin$t_h, Qin = hin$Q, Qout = Qout,
             V_hm3 = V / 1e6, h_m = h, saturado = vertendo)
}

# =============================================================================
# Cenarios de alternativa
# =============================================================================
# Dois arranjos sao testados:
#  (i) BARRAGEM CONVENCIONAL — vertedouro de soleira livre a 3/4 da altura.
#      Representa um reservatorio de uso multiplo, com volume morto ocupado.
#  (ii) BARRAGEM SECA (dry dam) — reservatorio normalmente vazio, descarga de
#      fundo dimensionada para liberar ~Q_SEGURA, vertedouro apenas de
#      seguranca junto a crista. E' o arranjo proprio de controle de cheias.
#      A_fundo e' calculada para que a descarga a meia altura ~ Q_SEGURA.
A_fundo_alvo <- function(Q_alvo, carga) Q_alvo / (0.62 * sqrt(2 * 9.81 * carga))

CENARIOS <- list(
  list(nome = "A1 — BAR-A 40 m convencional",   eixo = "BAR-A",  H = 40, Hs = 30, L = 120, Af = 20),
  list(nome = "A2 — BAR-A 60 m convencional",   eixo = "BAR-A",  H = 60, Hs = 45, L = 120, Af = 20),
  list(nome = "A3 — BAR-A 80 m convencional",   eixo = "BAR-A",  H = 80, Hs = 60, L = 150, Af = 25),
  list(nome = "B1 — BAR-A2 60 m convencional",  eixo = "BAR-A2", H = 60, Hs = 45, L = 100, Af = 15),
  list(nome = "B2 — BAR-B 60 m convencional",   eixo = "BAR-B",  H = 60, Hs = 45, L =  60, Af =  8),
  list(nome = "S1 — BAR-A 60 m SECA",           eixo = "BAR-A",  H = 60, Hs = 57, L = 150,
       Af = A_fundo_alvo(Q_SEGURA, 30)),
  list(nome = "S2 — BAR-A 80 m SECA",           eixo = "BAR-A",  H = 80, Hs = 76, L = 150,
       Af = A_fundo_alvo(Q_SEGURA, 40)),
  list(nome = "S3 — BAR-A2 80 m SECA",          eixo = "BAR-A2", H = 80, Hs = 76, L = 120,
       Af = A_fundo_alvo(Q_SEGURA, 40)),
  list(nome = "S4 — A2 80 m + B 60 m SECAS (par)", eixo = c("BAR-A2", "BAR-B"),
       H = c(80, 60), Hs = c(76, 57), L = c(120, 60),
       Af = c(A_fundo_alvo(Q_SEGURA * 0.8, 40), A_fundo_alvo(Q_SEGURA * 0.2, 30)))
)

cat("\n=========================================================================\n")
cat("ROTEAMENTO DE PULS — AMORTECIMENTO EFETIVO POR CENARIO\n")
cat("=========================================================================\n")

#' Referencia sem intervencao: hidrograma natural na secao de Estrela
hid_nat  <- hidrograma_gama(PAR_EVENTO, area_km2 = BACIA$area_estrela)
pico_nat <- max(hid_nat$Q)

# Decomposicao do hidrograma natural por fracao de area de drenagem: garante
# que  soma(sub-hidrogramas) == hidrograma natural, evitando o artefato de
# somar gamas independentes (que produziria "reducao negativa"). O
# defasamento real entre sub-bacias sera capturado pelo HEC-HMS/HEC-RAS.
sub_hidrograma <- function(area_km2) {
  f <- area_km2 / BACIA$area_estrela
  data.table(t_h = hid_nat$t_h, Q = hid_nat$Q * f)
}

res <- rbindlist(lapply(CENARIOS, function(cn) {
  eixos_cn <- cn$eixo
  A_ctrl   <- sum(sapply(eixos_cn, function(e) EIXOS[id == e, area_km2]))
  rs <- lapply(seq_along(eixos_cn), function(k) {
    e   <- eixos_cn[k]
    hin <- sub_hidrograma(EIXOS[id == e, area_km2])
    rotear_puls(hin, cav[barragem == e], cn$H[k], cn$Hs[k], cn$L[k], cn$Af[k])
  })
  n <- min(sapply(rs, nrow), nrow(hid_nat))

  # area nao controlada -> parcela residual do hidrograma natural
  A_livre <- BACIA$area_estrela - A_ctrl
  hliv    <- sub_hidrograma(A_livre)
  q_com   <- Reduce(`+`, lapply(rs, function(r) r$Qout[1:n])) + hliv$Q[1:n]

  data.table(cenario = cn$nome,
             eixos = paste(eixos_cn, collapse = "+"),
             altura_m = paste(cn$H, collapse = "/"),
             area_controlada_km2 = round(A_ctrl),
             pct_bacia = round(100 * A_ctrl / BACIA$area_estrela, 1),
             V_util_hm3   = round(sum(sapply(rs, function(r) max(r$V_hm3)))),
             pico_Estrela_sem = round(pico_nat),
             pico_Estrela_com = round(max(q_com)),
             reducao_pct  = round(100 * (1 - max(q_com) / pico_nat), 1),
             saturou      = any(sapply(rs, function(r) any(r$saturado))))
}))

print(res, row.names = FALSE)

cat("\n  saturou = TRUE -> o reservatorio encheu e passou a transferir a cheia\n")
cat("  integralmente para jusante (perda total da funcao de amortecimento).\n")

fwrite(res, file.path(DIR_TAB, "roteamento_puls_cenarios.csv"), sep = ";", dec = ",")

# ------------------------------------------------------------------- figura
cn <- CENARIOS[[7]]
A_ctrl <- EIXOS[id == cn$eixo[1], area_km2]
hin <- sub_hidrograma(A_ctrl)
r   <- rotear_puls(hin, cav[barragem == cn$eixo[1]], cn$H[1], cn$Hs[1], cn$L[1], cn$Af[1])
pl  <- melt(r[, .(t_h, Afluente = Qin, Efluente = Qout)], id.vars = "t_h",
            variable.name = "serie", value.name = "Q")

g <- ggplot(pl, aes(t_h, Q, colour = serie)) +
  geom_line(linewidth = .9) +
  scale_colour_manual(values = c(Afluente = "#8b1f2e", Efluente = "#1f5c8b")) +
  scale_y_continuous(labels = label_number(big.mark = ".", decimal.mark = ",")) +
  labs(title = paste("Amortecimento no reservatorio —", cn$nome),
       subtitle = sprintf("area controlada %s km2 | volume maximo utilizado %.0f hm3",
                          format(round(A_ctrl), big.mark = ".", decimal.mark = ","), max(r$V_hm3)),
       x = "tempo (h)", y = expression(vaz*ã*o~(m^3/s)), colour = NULL) +
  tema_sedec()
ggsave(file.path(DIR_FIG, "04_roteamento_puls.png"), g, width = 9, height = 5, dpi = 160)

cat("\n  figura gravada: 04_roteamento_puls.png\n")
