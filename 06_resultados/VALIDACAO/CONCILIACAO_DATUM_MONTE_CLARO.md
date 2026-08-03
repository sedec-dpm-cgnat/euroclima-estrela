# Conciliação preliminar da cota de Monte Claro

## Resultado

A diferença entre a cota usada pelo MDE principal e a cota da CAV oficial do SNIRH **não foi
resolvida como uma conversão de datum**. O valor do MDE principal em
`aproveitamentos_existentes.csv` é 132,5 m, enquanto a ficha técnica e a CAV do SNIRH indicam
NA normal de aproximadamente 148,0 m. A base da CAV oficial começa em 116,88 m e chega a
cerca de 157,25 m.

## Evidência de sensibilidade do MDE

O recorte público ANADEM, avaliado separadamente, retornou `NA_atual_m = 148,0 m` para Monte
Claro. Isso é consistente com o SNIRH e sugere que a diferença pode estar relacionada à fonte,
à cobertura ou à superfície registrada no MDE principal, e não necessariamente a um simples
deslocamento vertical. Ainda assim, não prova que os dois rasters estejam no mesmo datum nem
que o valor amostrado seja o nível operacional da usina.

## Regra adotada até a validação

- usar a CAV oficial do SNIRH para volume e nível operacional da UHE Monte Claro;
- manter 132,5 m como valor de localização/triagem do MDE principal, sem misturá-lo
  silenciosamente à CAV oficial;
- não atualizar a altura admissível de E09 nem promover MC2 com base apenas nessa diferença;
- solicitar à ANA, ONS/CERAN ou ao cadastro *as built* a cota de referência, datum vertical,
  nível normal, nível mínimo operacional e coordenada do canal de fuga.

Até essa confirmação, qualquer resultado de remanso que envolva Monte Claro deve ser apresentado
em sensibilidade: cenário A com referência oficial de 148,0 m e cenário B com a referência do
MDE de 132,5 m. A escolha entre eles deve ser feita somente com a documentação vertical da usina.
