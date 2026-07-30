# =============================================================================
# 06_sensibilidade.R
#
# A viabilidade economica das alternativas depende quase inteiramente de dois
# parametros ainda NAO medidos:
#   - dano_2024_MRS : dano direto do evento de referencia em Estrela
#   - TR_evento     : tempo de retorno atribuido ao evento
# Este script mapeia a sensibilidade da razao B/C a esses parametros, para
# mostrar quao robusta (ou fragil) e' a conclusao.
# =============================================================================
here <- tryCatch(dirname(normalizePath(sys.frame(1)$ofile)), error = function(e) ".")
source(file.path(here, "00_config.R"))

aval <- fread(file.path(DIR_TAB, "analise_alternativas_completa.csv"), dec = ",")
geo  <- fread(file.path(DIR_CAV, "geometria_barragens.csv"), dec = ",")

# A relacao B/C e' linear no dano e quase linear em 1/TR_evento, de modo que a
# sensibilidade pode ser derivada analiticamente das rodadas ja feitas.
BASE_DANO <- 2500    # R$ milhoes — valor usado em 05_analise_alternativas.R
BASE_TR   <- 100

TOP <- aval[order(-VPL_liq_MRS)][1:8,
        .(alternativa, arranjo, reducao_pct, custo_MRS, VPL_benef_MRS,
          VPL_custo_MRS, VPL_liq_MRS, BC)]

cat("\n=========================================================================\n")
cat("ALTERNATIVAS DE MAIOR VALOR PRESENTE LIQUIDO\n")
cat("=========================================================================\n")
cat("  (para alternativas mutuamente exclusivas o criterio correto e' o VPL\n")
cat("   liquido, nao a razao B/C)\n\n")
print(TOP, row.names = FALSE)

# ------------------------------------------------------- sensibilidade ao dano
danos <- c(500, 1000, 1500, 2000, 2500, 3500, 5000, 7500, 10000)
sens <- rbindlist(lapply(danos, function(d) {
  f <- d / BASE_DANO
  x <- copy(TOP)
  x[, `:=`(dano_ref_MRS = d,
           VPL_benef = VPL_benef_MRS * f,
           VPL_liq   = round(VPL_benef_MRS * f - VPL_custo_MRS),
           BC_novo   = round(VPL_benef_MRS * f / VPL_custo_MRS, 2))]
  x[, .(dano_ref_MRS, alternativa, reducao_pct, custo_MRS, VPL_liq, BC_novo)]
}))

cat("\n=========================================================================\n")
cat("SENSIBILIDADE DA RAZAO B/C AO DANO DE REFERENCIA\n")
cat("=========================================================================\n")
tab <- dcast(sens, alternativa + reducao_pct + custo_MRS ~ dano_ref_MRS,
             value.var = "BC_novo")
setorder(tab, -reducao_pct)
print(tab, row.names = FALSE)

# limiar de viabilidade: dano minimo para B/C = 1
lim <- TOP[, .(alternativa, reducao_pct, custo_MRS,
               dano_limiar_MRS = round(BASE_DANO * VPL_custo_MRS / VPL_benef_MRS))]
setorder(lim, dano_limiar_MRS)

cat("\n=========================================================================\n")
cat("DANO MINIMO DO EVENTO PARA QUE CADA ALTERNATIVA SE PAGUE (B/C = 1)\n")
cat("=========================================================================\n")
print(lim, row.names = FALSE)
cat("\n  Interpretacao: se o dano direto do evento de referencia em Estrela for\n")
cat("  inferior ao limiar, a alternativa NAO se justifica economicamente.\n")

fwrite(sens, file.path(DIR_TAB, "sensibilidade_dano.csv"), sep = ";", dec = ",")
fwrite(lim,  file.path(DIR_TAB, "dano_limiar_viabilidade.csv"), sep = ";", dec = ",")

# ------------------------------------------------------------------- figura
g <- ggplot(sens, aes(dano_ref_MRS, BC_novo, colour = alternativa)) +
  geom_hline(yintercept = 1, linetype = "dashed", colour = "grey35") +
  geom_line(linewidth = .9) + geom_point(size = 1.5) +
  annotate("text", x = max(danos) * .75, y = 1.12, label = "limiar de viabilidade (B/C = 1)",
           size = 3.2, colour = "grey30") +
  scale_x_continuous(labels = label_number(big.mark = ".", decimal.mark = ",")) +
  labs(title = "Sensibilidade da viabilidade econômica ao dano de referência",
       subtitle = "o parâmetro mais incerto de toda a análise — a ser medido no Eixo 3",
       x = "dano direto do evento de referência em Estrela (R$ milhões)",
       y = "razão benefício-custo", colour = NULL) +
  tema_sedec() + theme(legend.text = element_text(size = 8))
ggsave(file.path(DIR_FIG, "09_sensibilidade_dano.png"), g, width = 9.5, height = 5.5, dpi = 160)

cat("\n  figura 09 e tabelas de sensibilidade gravadas.\n")
