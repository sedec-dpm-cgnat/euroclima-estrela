# =============================================================================
# 04_cenarios_kmz.R
#
# Avaliacao dos tres eixos de barragem fornecidos em KMZ (Ponto-Barragem 1/2/3),
# comparados aos eixos originais em shapefile, e roteamento de Puls sobre o
# evento de referencia.
# =============================================================================
here <- tryCatch(dirname(normalizePath(sys.frame(1)$ofile)), error = function(e) ".")
source(file.path(here, "00_config.R"))

cav_k <- fread(file.path(DIR_CAV, "cav_kmz.csv"), dec = ",")
eix_k <- fread(file.path(DIR_CAV, "eixos_kmz.csv"), dec = ",")
cav_s <- fread(file.path(DIR_CAV, "cav_barragens.csv"), dec = ",")
setnames(cav_s, c("barragem", "altura_m", "cota_NA_m", "area_km2", "volume_hm3"))

# nomes curtos
eix_k[, id := sub("Ponto[-_]Barragem", "B", id)]
cav_k[, barragem := sub("Ponto[-_]Barragem", "B", barragem)]

cat("\n=========================================================================\n")
cat("1. EIXOS KMZ — SINTESE\n")
cat("=========================================================================\n")
eix_k[, pct_bacia := round(100 * area_km2 / BACIA$area_estrela, 1)]
print(eix_k[, .(id, lat, lon, cota_eixo_m, area_km2, pct_bacia,
                aderencia_BHO_pct = round(100 * (area_km2 / area_BHO_km2 - 1), 2),
                desloc_snap_m)], row.names = FALSE)

# --------------------------------------------------------- estrutura aninhada
a1 <- eix_k[id == "B1", area_km2]; a2 <- eix_k[id == "B2", area_km2]
a3 <- eix_k[id == "B3", area_km2]
cat(sprintf("\n  Estrutura: B1 (%.0f km2) esta a JUSANTE de B3 (%.0f) + B2 (%.0f).\n",
            a1, a3, a2))
cat(sprintf("  Area incremental entre eles: %.0f km2 (%.1f%% de B1).\n",
            a1 - a2 - a3, 100 * (a1 - a2 - a3) / a1))
cat("  -> Os volumes NAO sao aditivos. Alternativas reais: B1 isolada OU B2+B3.\n")

# ----------------------------------------------- comparacao com os shapefiles
comp <- data.table(
  par = c("eixo principal", "ramo principal (Antas)", "tributario"),
  shp = c("BAR-A", "BAR-A2", "BAR-B"),
  kmz = c("B1", "B3", "B2")
)
comp[, area_shp := sapply(shp, function(s) EIXOS[id == s, area_km2])]
comp[, area_kmz := sapply(kmz, function(s) eix_k[id == s, area_km2])]
comp[, cota_shp := sapply(shp, function(s) EIXOS[id == s, cota_eixo_m])]
comp[, cota_kmz := sapply(kmz, function(s) eix_k[id == s, cota_eixo_m])]
comp[, vol80_shp := sapply(shp, function(s) cav_s[barragem == s & altura_m == 80, volume_hm3])]
comp[, vol80_kmz := sapply(kmz, function(s) cav_k[barragem == s & altura_m == 80, volume_hm3])]
comp[, ganho_vol_pct := round(100 * (vol80_kmz / vol80_shp - 1), 1)]

cat("\n=========================================================================\n")
cat("2. KMZ x SHAPEFILE — o mesmo eixo, posicoes diferentes\n")
cat("=========================================================================\n")
print(comp, row.names = FALSE)

# =============================================================================
# 3. ROTEAMENTO DE PULS
# =============================================================================
PAR_EVENTO <- list(area_km2 = BACIA$area_estrela, q_pico = 18000,
                   q_base = 600, lamina_mm = 260, dt_h = 1)

hidrograma_gama <- function(p) {
  Vtot <- p$lamina_mm / 1000 * p$area_km2 * 1e6
  m <- 3.0; fV <- gamma(m + 1) * exp(m) / m^(m + 1)
  tp <- Vtot / ((p$q_pico - p$q_base) * fV)
  t  <- seq(0, 8 * tp, by = p$dt_h * 3600)
  q  <- p$q_base + (p$q_pico - p$q_base) * (t / tp)^m * exp(m * (1 - t / tp))
  q[!is.finite(q)] <- p$q_base
  data.table(t_h = t / 3600, Q = q)
}
hid_nat  <- hidrograma_gama(PAR_EVENTO)
pico_nat <- max(hid_nat$Q)
sub_hidrograma <- function(area_km2)
  data.table(t_h = hid_nat$t_h, Q = hid_nat$Q * area_km2 / BACIA$area_estrela)

vertedouro     <- function(h, L, C = 2.1) ifelse(h > 0, C * L * h^1.5, 0)
descarga_fundo <- function(h, A, Cd = 0.62) ifelse(h > 0, Cd * A * sqrt(2 * 9.81 * h), 0)
A_fundo_alvo   <- function(Q, carga) Q / (0.62 * sqrt(2 * 9.81 * carga))

rotear_puls <- function(hin, cv, H_bar, H_sol, L_vert, A_fundo = 0, dt_h = 1) {
  dt <- dt_h * 3600; cv <- cv[order(altura_m)]
  V_de_h <- approxfun(cv$altura_m, cv$volume_hm3 * 1e6, rule = 2)
  h_de_V <- approxfun(cv$volume_hm3 * 1e6, cv$altura_m, rule = 2)
  V_max  <- V_de_h(H_bar); n <- nrow(hin)
  V <- numeric(n); h <- numeric(n); Qo <- numeric(n); sat <- logical(n)
  saida <- function(hh) descarga_fundo(hh, A_fundo) + vertedouro(hh - H_sol, L_vert)
  for (i in 2:n) {
    I <- (hin$Q[i - 1] + hin$Q[i]) / 2
    Vt <- V[i - 1]; Ot <- saida(h[i - 1])
    for (k in 1:25) {
      Vn <- min(max(V[i - 1] + (I - (Ot + saida(h_de_V(max(Vt, 0)))) / 2) * dt, 0), V_max)
      if (abs(Vn - Vt) < 1e3) { Vt <- Vn; break }
      Vt <- Vn
    }
    V[i] <- Vt; h[i] <- h_de_V(Vt); Qo[i] <- saida(h[i])
    if (V[i] >= V_max * 0.999) { Qo[i] <- max(Qo[i], hin$Q[i]); sat[i] <- TRUE }
  }
  data.table(t_h = hin$t_h, Qin = hin$Q, Qout = Qo, V_hm3 = V / 1e6, h_m = h, saturado = sat)
}

CEN <- list(
  list(nome = "K1 — B1 60 m convencional", e = "B1", H = 60, Hs = 45, L = 120, Af = 20),
  list(nome = "K2 — B1 80 m convencional", e = "B1", H = 80, Hs = 60, L = 150, Af = 25),
  list(nome = "K3 — B1 80 m SECA",  e = "B1", H = 80,  Hs = 76,  L = 150, Af = A_fundo_alvo(Q_SEGURA, 40)),
  list(nome = "K4 — B1 100 m SECA", e = "B1", H = 100, Hs = 96,  L = 150, Af = A_fundo_alvo(Q_SEGURA, 50)),
  list(nome = "K5 — B3 80 m SECA",  e = "B3", H = 80,  Hs = 76,  L = 120, Af = A_fundo_alvo(Q_SEGURA, 40)),
  list(nome = "K6 — B3 100 m SECA", e = "B3", H = 100, Hs = 96,  L = 120, Af = A_fundo_alvo(Q_SEGURA, 50)),
  list(nome = "K7 — B2 80 m SECA",  e = "B2", H = 80,  Hs = 76,  L =  60, Af = A_fundo_alvo(Q_SEGURA * .2, 40)),
  list(nome = "K8 — B3 100 m + B2 80 m SECAS", e = c("B3", "B2"),
       H = c(100, 80), Hs = c(96, 76), L = c(120, 60),
       Af = c(A_fundo_alvo(Q_SEGURA * .8, 50), A_fundo_alvo(Q_SEGURA * .2, 40)))
)

res <- rbindlist(lapply(CEN, function(cn) {
  A_ctrl <- sum(sapply(cn$e, function(e) eix_k[id == e, area_km2]))
  rs <- lapply(seq_along(cn$e), function(k) {
    e <- cn$e[k]
    rotear_puls(sub_hidrograma(eix_k[id == e, area_km2]),
                cav_k[barragem == e], cn$H[k], cn$Hs[k], cn$L[k], cn$Af[k])
  })
  n <- min(sapply(rs, nrow), nrow(hid_nat))
  hliv <- sub_hidrograma(BACIA$area_estrela - A_ctrl)
  q_com <- Reduce(`+`, lapply(rs, function(r) r$Qout[1:n])) + hliv$Q[1:n]
  data.table(cenario = cn$nome, eixos = paste(cn$e, collapse = "+"),
             altura_m = paste(cn$H, collapse = "/"),
             area_ctrl_km2 = round(A_ctrl),
             pct_bacia = round(100 * A_ctrl / BACIA$area_estrela, 1),
             V_util_hm3 = round(sum(sapply(rs, function(r) max(r$V_hm3)))),
             pico_sem = round(pico_nat), pico_com = round(max(q_com)),
             reducao_pct = round(100 * (1 - max(q_com) / pico_nat), 1),
             saturou = any(sapply(rs, function(r) any(r$saturado))))
}))

cat("\n=========================================================================\n")
cat("3. ROTEAMENTO DE PULS — EIXOS KMZ\n")
cat("=========================================================================\n")
print(res, row.names = FALSE)

fwrite(res,  file.path(DIR_TAB, "roteamento_puls_kmz.csv"), sep = ";", dec = ",")
fwrite(comp, file.path(DIR_TAB, "comparacao_kmz_vs_shp.csv"), sep = ";", dec = ",")

# -------------------------------------------------------------------- figura
g <- ggplot(rbind(cav_k[, .(barragem, altura_m, volume_hm3, fonte = "KMZ")],
                  cav_s[, .(barragem, altura_m, volume_hm3, fonte = "shapefile")]),
            aes(altura_m, volume_hm3, colour = barragem, linetype = fonte)) +
  geom_line(linewidth = .9) +
  scale_y_continuous(labels = label_number(big.mark = ".", decimal.mark = ",")) +
  labs(title = "Curvas cota-volume — eixos KMZ x shapefile",
       subtitle = "B1/BAR-A: eixo principal · B3/BAR-A2: ramo Antas · B2/BAR-B: tributário",
       x = "altura da barragem (m)", y = "volume armazenado (hm³)",
       colour = NULL, linetype = NULL) +
  tema_sedec()
ggsave(file.path(DIR_FIG, "05_cav_kmz_vs_shp.png"), g, width = 9.5, height = 5.5, dpi = 160)

cat("\n  tabelas e figura 05 gravadas.\n")
