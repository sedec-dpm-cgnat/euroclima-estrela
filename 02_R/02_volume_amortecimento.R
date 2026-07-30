# =============================================================================
# 02_volume_amortecimento.R
#
# PERGUNTA CENTRAL DO ESTUDO:
#   Que volume de reservatorio (e que altura de barragem) seria necessario, a
#   montante de Estrela, para evitar os danos de uma cheia equivalente a 2024?
#
# Metodo:
#   (1) Hidrograma do evento em Estrela (observado ANA ou sintetico calibrado)
#   (2) Decomposicao controlado / nao-controlado pelos eixos de barragem
#   (3) Volume de amortecimento necessario  V(Qalvo) = INT max(0, Q - Qalvo) dt
#   (4) Confronto com as curvas Cota-Area-Volume reais (MDE 28,6 m)
#   (5) Altura de barragem necessaria + limite fisico de reducao
#
# Este e um DIMENSIONAMENTO PRELIMINAR, de ordem de grandeza, destinado a
# orientar o Termo de Referencia. Nao substitui o estudo contratado.
# =============================================================================
here <- tryCatch(dirname(normalizePath(sys.frame(1)$ofile)), error = function(e) ".")
source(file.path(here, "00_config.R"))

# =============================================================================
# 1. HIDROGRAMA DO EVENTO DE REFERENCIA EM ESTRELA
# =============================================================================
# Prioridade: (a) serie ANA baixada; (b) hidrograma sintetico parametrizado.
# Os parametros default reproduzem a ordem de grandeza do evento de maio/2024
# no Taquari em Estrela e DEVEM ser recalibrados com os dados consistidos.

PAR_EVENTO <- list(
  area_km2   = BACIA$area_estrela,  # 19.440 km2
  q_pico     = 18000,   # m3/s   — pico em Estrela (CALIBRAR)
  q_base     = 600,     # m3/s   — vazao de base anterior ao evento
  lamina_mm  = 260,     # mm     — lamina escoada sobre a bacia (CALIBRAR)
  dt_h       = 1        # h      — passo de tempo
)

#' Hidrograma sintetico tipo gama, ancorado em pico e volume observados
hidrograma_gama <- function(p = PAR_EVENTO) {
  dt   <- p$dt_h * 3600
  Vtot <- p$lamina_mm / 1000 * p$area_km2 * 1e6        # m3 escoados
  # gama de 2 parametros: Q(t) = Qp * (t/tp)^m * exp(m*(1 - t/tp))
  # volume da gama ~= Qp * tp * gamma(m+1) * exp(m) / m^(m+1)
  m  <- 3.0                                            # forma (cheia de bacia grande, pico arredondado)
  fV <- gamma(m + 1) * exp(m) / m^(m + 1)
  tp <- Vtot / ((p$q_pico - p$q_base) * fV)            # tempo de pico (s)
  tmax <- 8 * tp
  t  <- seq(0, tmax, by = dt)
  q  <- p$q_base + (p$q_pico - p$q_base) * (t / tp)^m * exp(m * (1 - t / tp))
  q[!is.finite(q)] <- p$q_base
  data.table(t_h = t / 3600, Q = q)
}

hid <- hidrograma_gama()
Vesc <- sum(hid$Q - PAR_EVENTO$q_base) * PAR_EVENTO$dt_h * 3600 / 1e6   # hm3

cat("\n=========================================================================\n")
cat("1. HIDROGRAMA DE REFERENCIA EM ESTRELA (evento tipo maio/2024)\n")
cat("=========================================================================\n")
cat(sprintf("  Area de drenagem ............... %10s km2\n", format(PAR_EVENTO$area_km2, big.mark = ".", decimal.mark = ",")))
cat(sprintf("  Vazao de pico .................. %10s m3/s   (%.2f m3/s/km2)\n",
            format(PAR_EVENTO$q_pico, big.mark = ".", decimal.mark = ","), PAR_EVENTO$q_pico / PAR_EVENTO$area_km2))
cat(sprintf("  Lamina escoada ................. %10.0f mm\n", PAR_EVENTO$lamina_mm))
cat(sprintf("  Volume escoado total ........... %10s hm3\n", format(round(Vesc), big.mark = ".", decimal.mark = ",")))
cat(sprintf("  Tempo de pico .................. %10.1f h\n", hid$t_h[which.max(hid$Q)]))
cat(sprintf("  Duracao acima de %5.0f m3/s .... %10.1f h\n", Q_SEGURA,
            sum(hid$Q > Q_SEGURA) * PAR_EVENTO$dt_h))

# =============================================================================
# 2. VOLUME DE AMORTECIMENTO NECESSARIO
# =============================================================================
#' Volume que precisa ser retirado do hidrograma para nao ultrapassar Qalvo
volume_necessario <- function(hid, Qalvo, dt_h = PAR_EVENTO$dt_h) {
  sum(pmax(0, hid$Q - Qalvo)) * dt_h * 3600 / 1e6   # hm3
}

alvos <- seq(2000, 16000, by = 500)
curva_req <- data.table(
  Q_alvo_m3s = alvos,
  reducao_pct = round(100 * (1 - alvos / PAR_EVENTO$q_pico), 1),
  V_necessario_hm3 = round(sapply(alvos, function(q) volume_necessario(hid, q)), 0)
)

cat("\n=========================================================================\n")
cat("2. VOLUME DE AMORTECIMENTO NECESSARIO (controle total da bacia)\n")
cat("=========================================================================\n")
print(curva_req[Q_alvo_m3s %in% seq(2000, 16000, 1000)], row.names = FALSE)

# =============================================================================
# 3. LIMITE FISICO: os eixos NAO controlam a bacia inteira
# =============================================================================
# BAR-A controla 15.760 km2 dos 19.440 km2 que chegam a Estrela (81,1%).
# A parcela nao controlada continua gerando vazao, mesmo com a barragem fechada.
frac_controlada <- EIXOS[id == "BAR-A", area_km2] / BACIA$area_estrela
q_incontrolavel <- PAR_EVENTO$q_pico * (1 - frac_controlada)

cat("\n=========================================================================\n")
cat("3. LIMITE FISICO DE REDUCAO\n")
cat("=========================================================================\n")
for (i in seq_len(nrow(EIXOS))) {
  e <- EIXOS[i]
  f <- e$area_km2 / BACIA$area_estrela
  cat(sprintf("  %-7s controla %8s km2 = %5.1f%% da bacia em Estrela\n",
              e$id, format(round(e$area_km2), big.mark = ".", decimal.mark = ","), 100 * f))
}
cat(sprintf("\n  Mesmo com BAR-A TOTALMENTE FECHADA, a area nao controlada\n"))
cat(sprintf("  (%s km2, %.1f%%) ainda produziria da ordem de %s m3/s em Estrela.\n",
            format(round(BACIA$area_estrela - EIXOS[id == "BAR-A", area_km2]), big.mark = ".", decimal.mark = ","),
            100 * (1 - frac_controlada), format(round(q_incontrolavel, -2), big.mark = ".", decimal.mark = ",")))
cat(sprintf("  -> Piso teorico de reducao do pico: %.0f%%\n", 100 * frac_controlada))

# =============================================================================
# 4. CONFRONTO COM AS CURVAS COTA-AREA-VOLUME REAIS
# =============================================================================
cav <- fread(file.path(DIR_CAV, "cav_barragens.csv"), dec = ",")
setnames(cav, c("barragem", "altura_m", "cota_NA_m", "area_km2", "volume_hm3"))

# volume conjugado disponivel (A2 + B; A e' aninhada e nao soma com as demais)
cav_conj <- cav[barragem != "BAR-A", .(volume_hm3 = sum(volume_hm3),
                                       area_km2  = sum(area_km2)),
                by = altura_m][, barragem := "A2+B (conjunto)"]
cav_all <- rbind(cav[, .(barragem, altura_m, area_km2, volume_hm3)], cav_conj)

cat("\n=========================================================================\n")
cat("4. VOLUME DISPONIVEL x ALTURA DE BARRAGEM  (MDE 28,6 m)\n")
cat("=========================================================================\n")
print(dcast(cav_all, altura_m ~ barragem, value.var = "volume_hm3"), row.names = FALSE)

#' Altura necessaria para armazenar V hm3 num dado eixo (interpolacao)
altura_para_volume <- function(V, barr) {
  d <- cav_all[barragem == barr][order(volume_hm3)]
  if (V > max(d$volume_hm3)) return(NA_real_)
  approx(d$volume_hm3, d$altura_m, xout = V)$y
}

# =============================================================================
# 5. TABELA-SINTESE: o que cada meta de reducao exige
# =============================================================================
metas <- data.table(
  cenario = c("Evitar inundacao urbana", "Reduzir pico a 1/2", "Reduzir pico a 1/3",
              "Limitar a cheia de TR=25 anos (ordem)"),
  Q_alvo  = c(Q_SEGURA, PAR_EVENTO$q_pico / 2, PAR_EVENTO$q_pico / 3, 8000)
)
metas[, reducao_pct := round(100 * (1 - Q_alvo / PAR_EVENTO$q_pico), 0)]
metas[, V_necessario_hm3 := round(sapply(Q_alvo, function(q) volume_necessario(hid, q)))]
# volume que efetivamente precisa ser retido a montante, corrigido pela fracao controlada
metas[, V_efetivo_BARA_hm3 := round(V_necessario_hm3 * frac_controlada)]
metas[, altura_BARA_m  := round(sapply(V_efetivo_BARA_hm3, altura_para_volume, barr = "BAR-A"), 0)]
metas[, altura_A2B_m   := round(sapply(V_efetivo_BARA_hm3, altura_para_volume, barr = "A2+B (conjunto)"), 0)]
metas[, viavel_Q := Q_alvo >= q_incontrolavel]

cat("\n=========================================================================\n")
cat("5. SINTESE — QUANTO PRECISA E QUE TAMANHO DE BARRAGEM\n")
cat("=========================================================================\n")
print(metas, row.names = FALSE)
cat("\n  viavel_Q = FALSE -> a meta e' inalcancavel so com barragens: o pico\n")
cat("  residual da area nao controlada ja supera a vazao-alvo.\n")

fwrite(curva_req, file.path(DIR_TAB, "volume_necessario_por_vazao_alvo.csv"), sep = ";", dec = ",")
fwrite(metas,     file.path(DIR_TAB, "sintese_dimensionamento_barragens.csv"), sep = ";", dec = ",")
fwrite(cav_all,   file.path(DIR_TAB, "cav_consolidada.csv"), sep = ";", dec = ",")

# =============================================================================
# 6. FIGURAS
# =============================================================================
g1 <- ggplot(hid, aes(t_h, Q)) +
  geom_area(fill = "#8b1f2e", alpha = .18) +
  geom_line(colour = "#8b1f2e", linewidth = .9) +
  geom_hline(yintercept = Q_SEGURA, linetype = "dashed", colour = "#1f5c8b") +
  annotate("text", x = max(hid$t_h) * .78, y = Q_SEGURA * 1.18,
           label = sprintf("vazao sem dano relevante ~ %s m3/s", format(Q_SEGURA, big.mark = ".", decimal.mark = ",")),
           colour = "#1f5c8b", size = 3.3) +
  scale_y_continuous(labels = label_number(big.mark = ".", decimal.mark = ",")) +
  labs(title = "Hidrograma de referencia do evento extremo em Estrela/RS",
       subtitle = sprintf("Bacia %s km2 | pico %s m3/s | volume escoado %s hm3",
                          format(BACIA$area_estrela, big.mark = ".", decimal.mark = ","),
                          format(PAR_EVENTO$q_pico, big.mark = ".", decimal.mark = ","),
                          format(round(Vesc), big.mark = ".", decimal.mark = ",")),
       x = "tempo (h)", y = expression(vaz*ã*o~(m^3/s)),
       caption = "Hidrograma sintetico parametrizado — recalibrar com serie consistida ANA/CPRM") +
  tema_sedec()

g2 <- ggplot(curva_req, aes(V_necessario_hm3, Q_alvo_m3s)) +
  geom_line(colour = "#1f5c8b", linewidth = 1) +
  geom_point(data = metas, aes(V_necessario_hm3, Q_alvo), colour = "#c26a2a", size = 2.6) +
  geom_hline(yintercept = q_incontrolavel, linetype = "dotted", colour = "grey30") +
  annotate("text", x = max(curva_req$V_necessario_hm3) * .55, y = q_incontrolavel * 1.15,
           label = "piso: contribuicao da area nao controlada", size = 3.2, colour = "grey30") +
  scale_x_continuous(labels = label_number(big.mark = ".", decimal.mark = ",")) +
  scale_y_continuous(labels = label_number(big.mark = ".", decimal.mark = ",")) +
  labs(title = "Volume de amortecimento necessario x vazao de pico resultante",
       x = "volume de amortecimento (hm3)", y = expression(vaz*ã*o~de~pico~em~Estrela~(m^3/s))) +
  tema_sedec()

g3 <- ggplot(cav_all, aes(altura_m, volume_hm3, colour = barragem)) +
  geom_line(linewidth = 1) + geom_point(size = 1.6) +
  scale_y_continuous(labels = label_number(big.mark = ".", decimal.mark = ",")) +
  labs(title = "Curvas cota-volume dos eixos candidatos",
       subtitle = "derivadas do MDE 28,6 m com flood-fill a montante do eixo",
       x = "altura da barragem (m)", y = "volume armazenado (hm3)", colour = NULL) +
  tema_sedec()

ggsave(file.path(DIR_FIG, "01_hidrograma_referencia.png"), g1, width = 9, height = 5, dpi = 160)
ggsave(file.path(DIR_FIG, "02_volume_necessario.png"),     g2, width = 9, height = 5, dpi = 160)
ggsave(file.path(DIR_FIG, "03_curvas_cota_volume.png"),    g3, width = 9, height = 5, dpi = 160)

cat("\n  figuras e tabelas gravadas em ", DIR_OUT, "\n", sep = "")
