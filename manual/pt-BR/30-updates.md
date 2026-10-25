# Atualizações

O Arch e seus pacotes são mantidos atualizados por _Atualizar > Arch_ no menu do Arch (`Super + Space`).

O próprio Arch é instalado como pacotes comuns do pacman a partir do [Repositório de Pacotes do Arch](https://github.com/kairosci/arch), então uma atualização instala [a versão mais recente do Arch](https://github.com/kairosci/arch), executa quaisquer migrações pendentes para sincronizar seu sistema com o mais recente e atualiza todos os pacotes do sistema a partir do [Espelho Arch do Arch](https://github.com/kairosci/arch) e do [AUR](https://aur.archlinux.org/) (se você tiver algum pacote do AUR instalado).

Quando novas versões forem lançadas, um ícone de seta circular aparecerá à direita do seu relógio. Clique nele e o processo de atualização começará.

![update-available](images/update-available.webp)

### Quatro canais

O Arch é atualizado em quatro canais: stable, RC, edge e dev. Novas instalações começam no canal stable, que acompanha os [lançamentos oficiais](https://github.com/kairosci/arch), bem como o [espelho Arch stable do Arch](https://github.com/kairosci/arch), que está um mês atrás do mais recente, para que possamos detectar qualquer nova incompatibilidade que exija alterações de configuração antes que ela cause problemas para as pessoas.

Mas se você quiser ajudar a identificar esses possíveis problemas, pode usar o canal edge. Isso manterá seus pacotes do Arch acompanhando as compilações de desenvolvimento mais recentes e permitirá que você atualize para os pacotes mais recentes do Arch assim que eles estiverem disponíveis. Você só deve fazer isso se for experiente com Linux e souber como recuperar um sistema com problemas.

Antes de qualquer novo lançamento importante, faremos a validação final usando o canal RC. Se você estiver interessado em ajudar no polimento final, venha nos acompanhar em #arch-release-candidates no Discord.

Por fim, há o canal dev, que vincula o Arch diretamente a um checkout git do código-fonte em `~/arch`, combinado com os pacotes edge. Você só deve usar esse canal se for um usuário Linux experiente, trabalhando diretamente no Arch e disposto a tolerar quebras.

Você pode alternar entre canais usando _Atualizar > Canal_ no menu do Arch (ou `arch-channel-set` no terminal).

### Atualizações de firmware

Seus pacotes não são a única coisa que fica obsoleta. Muitos notebooks e periféricos distribuem firmware de BIOS, SSD e dock pelo Linux Vendor Firmware Service, e _Atualizar > Firmware_ no menu do Arch buscará e instalará o que quer que seu hardware esteja aguardando. Ele instala o `fwupd` na primeira vez que você o executa. Muito firmware só pode ser gravado durante uma reinicialização, então não se surpreenda se lhe pedirem uma.

### Aviso sobre atualizações diretas pelo pacman/yay

Se você já está familiarizado com o Arch, pode ser tentado a simplesmente executar `pacman -Syu` ou `yay -Syu` por conta própria, mas se você fizer isso, perderá o snapshot, as migrações e as atualizações de configuração que o Arch executa junto com os novos pacotes. É por isso que o Arch na verdade interromperá uma atualização direta do sistema e o apontará para o `archctl update`. (Se você realmente sabe o que está fazendo, a proteção lhe dirá como ignorá-la para uma única transação.)

### Revertendo atualizações ruins

Se você algum dia tiver um problema depois de fazer uma atualização, poderá reverter seu sistema para o snapshot tirado antes da atualização. Basta reiniciar e escolher no menu de inicialização o snapshot de antes de você iniciar a atualização.

![bootloader](images/bootloader.webp)

Se de alguma forma seus arquivos de configuração tiverem sido corrompidos, você também poderá realizar uma reinstalação do Arch usando `arch reinstall` no terminal. Isso reinstalará todos os pacotes padrão do Arch, colocará você no stable, fará downgrade de quaisquer pacotes que sejam novos demais e redefinirá todos os arquivos de configuração. Observe que todas as suas alterações de usuário nas configurações padrão do Arch serão sobrescritas ao fazer isso!
