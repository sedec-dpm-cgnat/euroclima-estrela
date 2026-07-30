# =============================================================================
# 01_baixa_dados_ana.R
# Baixa series historicas de cota e vazao da rede ANA/CPRM (HidroWeb legado,
# endpoint SOAP publico) para os postos do Taquari-Antas.
#
# Uso:  Rscript 01_baixa_dados_ana.R
# Saida: 01_dados/ana_hidroweb/<codigo>_<tipo>.csv
# =============================================================================
source(file.path(dirname(normalizePath(sys.frame(1)$ofile %||% ".")), "00_config.R"))
suppressPackageStartupMessages({ library(xml2); library(httr) })

# tipoDados: 1 = cota, 2 = chuva, 3 = vazao
baixa_serie <- function(codigo, tipo = 3, ini = "01/01/1940", fim = format(Sys.Date(), "%d/%m/%Y"),
                        consistencia = "") {
  url <- "http://telemetriaws1.ana.gov.br/ServiceANA.asmx/HidroSerieHistorica"
  r <- tryCatch(
    httr::GET(url, query = list(codEstacao = codigo, dataInicio = ini, dataFim = fim,
                                tipoDados = tipo, nivelConsistencia = consistencia),
              httr::timeout(180)),
    error = function(e) { message("  ! falha de rede: ", conditionMessage(e)); NULL })
  if (is.null(r) || httr::status_code(r) != 200) return(NULL)

  x  <- xml2::read_xml(httr::content(r, "raw"))
  nd <- xml2::xml_find_all(x, ".//DadosHidrometereologicos")
  if (length(nd) == 0) return(NULL)

  campo <- if (tipo == 1) "Cota" else if (tipo == 2) "Chuva" else "Vazao"
  out <- rbindlist(lapply(nd, function(n) {
    g   <- function(tag) xml2::xml_text(xml2::xml_find_first(n, paste0("./", tag)))
    dt0 <- as.Date(substr(g("DataHora"), 1, 10))
    if (is.na(dt0)) return(NULL)
    vals <- vapply(1:31, function(d) {
      v <- xml2::xml_text(xml2::xml_find_first(n, sprintf("./%s%02d", campo, d)))
      if (length(v) == 0 || is.na(v) || v == "") NA_real_ else as.numeric(v)
    }, numeric(1))
    data.table(data = seq(dt0, by = "day", length.out = 31), valor = vals,
               consist = as.integer(g("NivelConsistencia")))
  }), fill = TRUE)

  out <- out[!is.na(valor)][order(data)]
  # mantem o dado consistido (2) quando houver duplicidade
  out <- out[order(data, -consist)][!duplicated(data)]
  setnames(out, "valor", campo)
  out[]
}

message("=== baixando series ANA/HidroWeb ===")
for (i in seq_len(nrow(POSTOS))) {
  cod <- POSTOS$codigo[i]
  for (tp in c(1, 3)) {
    nm  <- if (tp == 1) "cota" else "vazao"
    arq <- file.path(DIR_ANA, sprintf("%s_%s.csv", cod, nm))
    if (file.exists(arq)) { message("  ja existe: ", basename(arq)); next }
    message(sprintf("  %s (%s) - %s ...", cod, POSTOS$nome[i], nm))
    s <- baixa_serie(cod, tipo = tp)
    if (is.null(s) || nrow(s) == 0) { message("    sem dados"); next }
    fwrite(s, arq)
    message(sprintf("    %d registros  %s a %s", nrow(s), min(s$data), max(s$data)))
  }
}
message("=== fim ===")
