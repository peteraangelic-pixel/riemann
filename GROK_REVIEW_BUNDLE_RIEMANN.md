# Riemann / Kaggriculture — code review bundle for Grok 4.6

## Review request

Please audit this project as a competition agent/research engineer. Identify what is methodologically wrong, what is missing in the closed-loop integration, and propose a concrete stronger plan. Do not treat open-loop replay mirror scores as evidence of a champion. Focus on: B21/S16 control, G2/G4 overlay semantics, reactive planner correctness, Rust/Python parity, same-seed paired-seat tests, crashes/timeouts, TOP15, historical TOP30 transfer, and fresh holdout.

## Current status

- Development corpus: TOP15, 15 teams x 7 selected slots, 105 slots, 94 unique episodes, 720 steps each.
- Curriculum: TOP5 -> TOP10 -> TOP15 -> fresh holdout.
- Frozen control: B21/S16.
- Best current open-loop structural profile from upstream G4: 29 wins / 83 losses on 112 TOP15 mirror games, team-balanced score 0.29333. This is NOT a closed-loop champion.
- Our simpler G2 market overlay: 25 wins / 87 losses, team-balanced score 0.2600, mean margin negative.
- Required promotion: both seats, same seeds, zero crashes, positive material margin vs B21/S16, old TOP30 transfer, fresh holdout.
- Current R1-R4 modules are partially implemented but not yet fully adapted to real Kaggriculture action schema.

## Important warning

Static replay/tape agents are not adaptive opponents. Market overlay scores are open-loop diagnostics. Do not infer opponent adaptation merely from replay action patterns.


## B21/S16 frozen control

### Source: `kaggriculture_meta_lab/agents/current/agent_v9_b21_s16.py`

```py
"""V7 with isolated two-seat t0/t1 wheat quantities."""
import base64,copy,json,zlib
BUY_WHEAT=21
SELL_WHEAT=16
ACTIONS=json.loads(zlib.decompress(base64.b85decode('c-rlKU5^_{lH`Bs=X$7Ok@azJnr`m4u$r!hTD`>HfEWyLyIA0`_b_*Fhx_j*sfsLSy1ALTM^vkOu}>mcRAywPM}&Wvng8W4|M$Cp``h3D<6r;&-GBSbcR#=T<(Kb{SKs~n-~QMC_}`zu`26ud{`U9(`LF-y^XI>O_orX~<*z?~eEQ+n?>~Ka_1)pe{kzZqZf=gp|95qHk)NJEe)=)L$}js5A720a&E4_p`O3fS_dmRTf4}<r&-)KgKYjlB=F9g#zW=!Y&i(M^BJX~B|L1pK?)v@H;q#Eg*T4L@-~asO535Hx?0@-m`6Qob=>7Nq^y|+rSNd|Dm!G^o_QhArAJb{jcYeM8`LfT$Uf%rm)1Q8Q|KW$fetxB&e*H2P#=8uo`1!-TpFW*ue=(fZ)h~zje6{6Zz?eT@{QJE(Ialt05AQzhKd#=`<!$f_10(<bU7WN2sKU#9zWf!O#?_o(jQIJ(q(PB)`)a^1bNBkvP7@sM{q5f1>z)4L%Vw~ck~n`;N3(wyHh}PY&hL^;+v<P4+351uvzWc-Uridt%kv}q0fSi0)+}RQ9bD)=U99()zr8N^%U74ZD7mO#Cm*a~^kU*`&@cGB7k~?fPvp|0GZufn`pp|mUHCLQbuT}<eE(mkr8RG_b926IK5ZA@s5_3&*7JC35B2;FoUHTTI+L~hzhp*cUH@XT=8il0z%IM?GZGg$^JcYSWE(FTRB+d!KLoy#SAIEfoRgefB_1#5|9d`5^mh0C(}xfH??3(ZANC(Vz5nq3zps6a^QGVqsWUA%p5&4zFJbjHITtT}Ne;)`wVnL(^y~T!pT1IVob5`+Cjl<_>PhKw1s{5I^cO1d43XQ@_AgHN2~*kIS6(mkHp2u9c<5MI?KG1|%Uo6eD#^kdFm!USce#}{PM0BDTAzJ`R~fOB|GYz~p7vMU@_B#xfgJ(M)LGd7<2f9cG08E=^EllUrku=US4Z9rxu7-;GMT+VjLl~&^06oM?9dmyMUW948?7~;bF34MPhQWROf*>e@W3-e!#!Q_$9Et9x$bnw_Z{O$9kW{#dmi9iLw)s)Vz8(e7|7v`nJjQ;7n?iUV$O39-yz)Ix43!{oswlqf^YMUH&3_F7+mZ5V;8(gIr(S)BExSE^TnoSB>`so6dmW{cF4I{6w8+0#IBHakRM9>R=miZ17Xs2#pXqv0TDjw)nes-t&5Xc4^9zEI<xfsgHb4;4{~{$jQf!xz-HTFH^q!k!npf7CpmiY`!unPrqbWzfgONJB2(D&9FUD&&Ya$){pbNaMdzh6mkl^r;kKif&gZV^vD~^hV%{=zTy9OrrQ!dfkfrnV>ORQQ<C&a9<-Yx+8~Q!~^P?`Vw??e^H?UvOX@*fj)xTRlPtlQ`UV~a-MEZW%ZpaTq?$`3`&y)1=>C?p;d-?vCPaoeM{<Q!2@n3)iI=<CvimmMERd)d(tW<vgw&&HjI9O9j78yh;{ls#7L+jd>NDlYG8mJUhNJIN>*W3pIi6~WNV!@h~U@a~(7JfPoAlVQvousUiK51jmiu1FwTMc8_92-fm!oaOuSM62W6Rz+PEaEa^^`R67ndbPx@ZF6AzjC?$9P5jdBw}YKOPAA52ypLr{j0;ha7XsSN?CqFu4}fBwXJOPrSw-EdEDK4H%(Jk=i+%2n3F;_dn0GQAG#G-!vjm6WUegd#zR=0FD)mY=JL=G<J1?DL?G`}oL@fPPCb^wyU|?8Iem47WFqeD3&?3b9l95`y}16u|3bgLyjg9|F@*u$p;geNuM}h<^w9_gj4F*wXipRG3jJRBHrWW1xuqDQn$HW<%|p|RvOM<mT3BCyZc9gfaWYHSo&pUD8KI>MG~^}8Q+=Rr=eRkWB$aei@$5XbaF%$1E|JQhK<qQz^+8dTj-`|Z(+fSalj1GqZ>lF9U>}8>vRsn9tBq&Q^E+3K|6_zZho`3x&y>)SEKmZEpjnAi*nJ)VOOd8a>*a5s51=0srs{3H@)8bxl^{ptJA9pw^GO&#oQ*a6jT5v5R7Sii7|hvZom<=R-IRZUZWszD)T6s1b2=s89LEI+M_@|Vqv}lD8cPoiDFW`}H*ugTqN}tO<VLorhA)adka`Ol8D8vIq-j)Y0Ev?tR}$rvP`dHurDxPQGwl6qD4J8CDO0b{j&M>p(LfnosFOiJrR50OSciHNz^5|B-6^st*Nk;sfr@}wXU(e+yWL?09jR@5SB;E1C7F-_(~s%J6%4*Di_rH3vl3CO>V@_V?P6Vo#mIa%|ExvzC=85oW}ji0>TfIo(iCz5_!W5|Z4X9cvR8G2-HAMJ`=M{2EK4OpI^^1eicyn$(U`i)&c(@rWrl)=8#ds>LX`p!jR}2>@Pya-^vfGWGVweNaJ*Y`SiG{21r6CBn;o`aI+@6K%>G-6)I5Re8y`r;V|f5a0fm0lQRF*=yDqS(=>LFBx;uj|43m|R;`q)GIrXBwne{dlFvJ+wrFI=pY7a&_V{AEak&i|mEYTA{LKi9a6P|gMh{Bg!VcZ_+G7U<;r1`un&W>6y(9&HImNx^KR${<T_>`7(t{_HAy@XCaD|+$d8!zIo)b|`<JM!T>Z@%=Xak)_q2qRQZjzMev^(YImrWUPB1yF29oI|TiC4dBzM()BRIziLelT*uvO_<cCRiE3Tg5XwVcAUt69L~$?d#r+yC*CdBlGpfRkz(47Pbbu$-+%b0P*khM01)9-m8*-=7q25rl1z6_Xd5+OMa)}J^+<hD=`54{bNZut`iL?LmjbQN^Mc-A9+9XadTLcMdBB$2=)~zdMy#Eivyvm_I@2O^4Llx43a(U35)xQjY-Nyrffpz86qTT0rk(lK7@SmPMF`*WICHr%*nwG_XNG%{+Xp7P9|*`IsvzSL!opuin$0k`2(w^*Dl6EK^T6kU#T#IfkyDBp*M5PtF*lH)6%K0~v%J4rSOKzs9mY+JuMXBbq7d*NJy*q>Y<>{)dG%-`xPO8_v?j?Xr&NlH*34uwyFOLt_ShFJYKE=VA#Q6}*jg~Uoe=)Q8lncjzPx7?(mL!QQ#vP)ZgJO(7nlB~80wImZdRXz!Lj#9-Z2`-Bnx<poh7!RXlNCI+FGq{ccoE&c9`6qx4{Bl{ZqZPV!>8v`IrZ7i5A<iB?1ot1VPa!&S6YN1Zl_@p{G~%V011H&6tmMmEb`J9e(|)5PqT33B!l132HKzz67m5FhKbOk@ilvb|;VcIv<{eqJ;dunsZH<bpV1LcXI5=OY87@Ah>4BK#BP#nze)=AABlP12vA464Z3bXa;5uARpk~6muUPAqTh$SllfMD|DuGy(l;SG-wcu0R>X2SlATAp@iM!#_t(iPg#T@=3p3{6HJDJzpSN<!5^6(h*FG98j_-w>CBC1P<)sq8pawI<ylK;o7(Kpw%ZAa$8_DSV0c#Hw~C%6A6W60_Z<;!9KG7z?LfmE_b~=yczA~H264;orx?Hwg3o3Q3WOeTeg|a3gjxhIQ*#e9+0`$P?R8vQ$}wDC2>SxKdY64>tjo^$fNO_u2OJebIpv4t=m@EQ41UHC7>*Da^BBPGfEaF;Jm=}0m;SkTV2<JGc=>z0vbKEl-6dp!hb%e$ddEbjBRq$Nr@s6T=(~(oyK=rk9%emPn{7H-J13J228Y%Re?*dxRjEhg5pPO*5Gb+5-y`uQB9|gePS22c9q5{DZj790c;tyB+^g5Qo;d!rhAfTM2N^v_B!D72m2{KUq;;Gle3~zbs^337{fyi5;*~};))ApdP)``uuk*6NvBShV3Ai<y7()vVy%C}VU}BOR3uX}V7_;-|F#{4kqg8;cwR#Aat~rlZVv%!sfQ!b|4h|Z+u<AJRJ7y9PIY_e$Mr(WynoC?xNNJFVM2M^mGfyTkmXkW#UaGrpIiUf#igk^!PR7Jm6dM4!a2P^xh7vyPEe6ov+%$O5kCXE@+~2KBnD*HPSof%jRp6O^srIL!lQi7}{8!)+_RA<Fkae^(ammMiWLb=2ReFLG0oyVvJ@1{uqc@Ms^ZrhOl#>~9LT>c`6f%Uk4#W?*KNi$8W!)heI;U|YP)+DPwW^3j{Fv&^G|WHGMV3S!zyeU~O_?2qWy~NLP{RR<*_xG08{Fr*OD*23m+Zi^SO6cp{QNdT#s~T*DWWWfrC^#?6UQ7duTTdOx+m@Et!5b==6Oh=#!LR|;AE3Mtq@}{^*!GAZDglmG<Bx;#rAj`SUHLs(MqO5tS{g4k%1}b-IC|A-5m>}2u%6`yb&-=wMrq%rw*^B>^c<-(hc5)Vss_HCCck6Q(MU_f_D;bX|q%1-r5nu+U2z@6O4@=AZnSeUc(f*7cS<JGf?Vh##&jVDI0GH5L`8XJ`>jR_zhq!mPEm>kQ^W^2v)XQ*x+5Q?g7daHFid$v@Wo_`?P%CpkIIuR{?V4?d%^Gp!iFS_qHgSzW&cPsD{0`6}0@Wq+Z2{_mpB$0Nz7Wj@GnZTN?>kN26&S=C*AWz{8}lUls>ZhDG0$Lg@J2bx~F=ZacKHW7IEGUTrBq6Nh7fw|E9-tk1J;W3~@o6}xN8OL=g50tzqaEgc+6OFUy{<vbWF*nWe6rr7D@bl6uph`?vFJy5(&bW)=-ABS1|j{bRN_DIGM0KEyBAIxeY)c}rPaQ4Mp#4)1mU#lIPZAK|^pKp;hAb=P{!KSBnj$)JrA~n!y6<RBvPo^UHtv6BJa*ylakKZ_)8$|Kfi{gzY3l=7lM0KM|b6_Aj@RCP(9V~evu}C@2Rl0q%%#9M{(l2u%qGP8B?bpencDX~>q@%O^J?zuT5`4`(zI-iCdLBd1OxAjr!)Lb3#qZo`vt;27?kYN&48}o=g{i~dj6(&7761hhXw$0Psrjl1aS$h*L1hYgh#@sK=8GHgw3+Sih-9G*C~9)66_}Z?-Ba@emPKjN(f$fk)0FGu<UE2!H)DpToO*$E$8$8P_+Zb<NYWS{Ypj3o9EnmZyOuU*{!MI*Dvu!4OOCQOp#CI+L*9mT671^pP^8BlLniD_K6GYFXxsFn&qB+oOu6pcmk@!!%hhdpl@RfeYzj1r!LI}ETKAHDt`%*J@OtfYi9mwlmIY6lI$2kytb>;zK#>`AAu&C7IV-oTKZZgUd9d3`>Yx;pFz-7O<z8o*QHHU@doYp=OlpD7W=xz!j*Obq^VHP(I${9cMG5yV33&l{Fc4@~OYz=-(4oWv7!aBKgKISC?_~52`<caz1smRvXuxHLfL4AEY)f+S-~lC_tI*?xL^6Pb!Ss-bRTeU0W~L5HMU2{C!Q2W`3am9N5S^N6cvOkeW<huz<SHt7MvTvLj*vBu7Tb^-35$C`1XobZ&QfZ_nOYhUVeEzp(JmTZE3eH~N1kb$vJIx1e5&t78hAFr2v9nos?I3jD#)DmATNXwOij^BDjQ%NtHpN=_9>q}PoNcHII5So4K+uF>B%VGCWqP_`jnz@#)1Bgi@!maNT38MC6lSut<TVu`;24oZAK{HR5+0_(-2f2^Kf)m`%-J<)e-jAvjN4YSPh58MS&!30Iz80H3m>48l=&Qs(KZ#C%dwDh4`_7e}!2TI((P8qss>=xFJm5Zgh6-JQm1-`65E2rS5F%h-*x2lr2Jsip1zXG#%A6PbgZGJ$m!?Uq%v(x!${EK|_SGZvY5H#HwM@MrBYu8m2Ah?T7dOm~Vr`Hfc7d$7QBL%;lH~U8`@f1SM2SZE_}SOU{(_1TaTkGz#WpfYUW9<~<8$?N~pCXEjShc58d=Y-?<-MQc9jyiP5wp{{MjI~AL9kcaF5p0ZP`Qv7FG+LU(NrTBt5g()zKq|A+`3m5ZP7;)Kv<A<pR8;Gn+Ije_cw5nwvP#tr{Y#>2kjMeQDBs%J33TMy)^;?)NE1_V3&kK9~x3Ax`WQNqsHVK+Mo?c1TyXtC894*zQE65PPmRn79Jk2|#*NLuq3Vm;?(U1@EMG_X7w?(&A1c+dBs{HOA-Ms5gFIL~@;R-{u6x_-@30(^_>$k?so>FSj%r+UlZo34=%D&LU#qQJ?iw~60e0H&agj>Ci3kv(fw}H4HKZ2*-z`Jgo-wJOTE93Ovg}VnstWHJ8bB;}-x!{U7d4<3c-KOU}sgz|KaWpWy59mnOQA;<9Rvk;J2qFkZdyn7iUg&Z}qPYlo$TWq#uk+3$=K4VHOw(?xNodi-cu8G6UbuVDURx*^$$r@c5wS{?Jfy3dlr<8h0+BO&zS(`HBP?sp!nFLFEl7*u<@wPrH=$VA8(A8HFb~W!iMsuSZd@1~{2YbXm$Ly~aYoodi>^KSYMGGq$tiO!-a%|rz*QC-)O1U@4{C)fO?ATZXDI-cqz0n(HdX-}unl?uZ3ahJ5)6K^2&*5<sEyWCZ;lg@8{a~WjW+p?1c`v9Fq!@^@83$jYzGARM^F|XYNY_mxGy{iD{a%k`1p)MuHMqIW-wDx9f@bzShIH76vl4sT<9;w(BZV3R-w+w2Sy<jCSIk&W41DG(feJ-4uU>zVAw0TSCJed{<d4GAe>(2rWZ<}{Sx>H%^VPyS`bmHj!3QAj5*;B!_i6W80lEE8iw&;qqBv!GfG5lnt5Oe?SyX?hWN>BNpO_|%93<)^-!6L9u~{1lq(_%5g}s>xjOMMTbHo#o(ZtH^_NXfaNX|nEerEa@E=P9VX8Rj`IZcbcB|o<aZ}TjXtL_W7aAvej8~Cnqypca$^>PT8e)1n!(Iqz+4zVmArZc-iBF8ZU|YA4sc$eUN))CnmK?rpMR*G+OBVY26I2@_--dC<?B?h+91IVBH=)tr81Cfvo%o1JUl!=+=?;t9Aj0h(g+JaJef`>*5m9N9N*Y_8=^_2-cz=~Lj)vDbS-UGzFo);k3b4};D4F|DRRLcQ2Py8GK!ZAGCo3w+8Wn@Dbbzc1e@}%LRUqNFioJ9rqVL%D0im0c1TPN4IPH&PH&?h*@J2NEf|;(&nD4-wF4|p`jL=4cI7CX~5Ws+jwH<QEiO?!6h@*~C2{Ob6b4aCQ#(-D-DUV)&rC|WezZ4o)!F&vtfSKYxNTm}!5<px}*WtKo9ZiVjwr)3?;RWD22^CLz*Y{vL(1Yy?55zPMB>AiLS!iCZpMK<J3D$K976#I1l;PK%0T$uOfQ+RGHfT$C!HI+kcFOBMnT66`(-yJ%us-K-T<q^I)E@*+3d3>`z{f-`Dd06^`)_IclkQhKQzRGr=!+OG-so2CnWXy0iVmK3^yN@OB|a`FmfC`<Lft0KG>R!VeEc1ee^v@1G=bdU^;DES&4kQFo495^29ty~$H~+hri4M#F|A|!V39UT0x6_CGd5OUNM@`W=?U53^R_}*3v@ys#Xv1}$&bEB2WNE<v#kV7G_)r5pe(ZFrScx*N4|E{O1T6>nW2r)Y4fGxq#iOQslC<Qu!hzE<}tBWqKu_L(;1=@c{g7hQG{8J(cx&46i?mSksYH7i%7lsN;W#*Q*3Dm?Neo&5n*WWixZ~WhV8taZz7uP7~K*-1Fg&?1^{#!F-(@@nY2s-3|6516&H*-NJFemV22fvV4r)eu2j(BN=yW0vpH>tR-<$khQ!57H4betQB8bBqoi)U!ih0)YV#qs8kE5L)N#7KBay~oS~UhqhMtf%48%oA(ZKJQ&QJX$V{xV0juY;TEw-A^m7ns61fbM=laIYAJS5ZyCXGY!GNS38KRPIeIlGRsEAO*HQkSLd%;rs4Llz*&cmzu&m6U;CE=%HLHrG03nKx+g<u%9_?z8Guramj4a8c2Ml7wu?F@lcv^~ICgCJr!*>ITE5LN`N0DH&EaDTo(b>$O=D-VkUH#-*zuA>xXogfZYgRFX_5_H(88fLeHPqLzayHJKbuL9xP{)1s<M(@9hi_m0Sfud8=)pBWYMxP_}qdOU`3U^D`sL7DTItR!rGB(7ekIdP;+w(?3wZfw#5n5y+$HvM9EX4P=5^DvAb1b$LS;PF6)7_2<2#|-V#qY13hzNxYg?fT^Rj|LbW4XvVfE-@&KOvb9QtCc)(^faa{2dSXR)CrvM@EU}&Jr>w9#4D1rgRJ~jNl!A1W{Sxy#X%&ow6JieuQQb%Hx<m3JI#E?3iid&w~<JgRv19(EE3x)P5;qyu2NZ2(ni-(o*O4Fu0ct^M=ch}wlSq)eF5B!8%MsmHm=2nq@5latTl(p^n(7Fm4=-SSqDZMJp02V{ay`MRu<y>BX`QyaBgS8SvV&?e~3}au23yOyI86?%tFkWHcR|MtC3Bf?I^_p71J%iC!IsoqIyp^W%m=49@S(frdf6!sz+PUTJ5H_UE{n+CW<Rcmt=y*R|1#$HajQvv`*@)pdek+f|PV(Jdm=Iv_9OgB5}kSXUQWru*I-&!K;0J_CkoCA5P*SyGH<%K7*k?%8B#FOG4qa)b))|F_Mb0f<CR%kRN3|Wgmn}!a0Y+;Xvs@G<PvWSP6w^R)aI4n$i~bxJx=Z=LLN#SnYMZI(TS|DCHP&39*tIM;yZ%n$V=DX9*Ky%h56w7q!vFSH<xzC(lHV-f;D7xmvV2QoK(F6q%-K>&Ud|yjx9K=MO98k_)%Es1=q7SG=LAETNmnik!>p+~z7ZT+6{muaxr6UUPA}8&`DbO9^IhSEr$E4F@L`NJdL4c?C$(KB+y}t!5f&E82^e)}N@aOl$Lf%72IOZ0UXW!dy~~R|P<??k8ILd_|;8P_2+FM*%DfS)m&AwAt!|dYN2*C5xqCz$lCxx~jLwQgJ@nM}(<6HA6~9?Bo$yvLK!pTsI0NZmH#))nY!^UCyamRpwFVbGew*DpMR0JyA{wx1#8AGvUVdLOcM9@u$2=)Ns{4dQS&$m!ze&QS3>QuFqA_d6O^7|D1t8p<*9>APU>?WXi<>&+;}qR8fEy*IB%ITA`qd@AU?v4Lh0DgYl6(3Jcho_OD!+44Z=VVu_G1<F3Y^>yfo_Cw_M#E5&C2U#Tl|Q=&9Ejg{%_L)On9MgO)8E!kD{R))bMQ&dw7ngB=(Q#Dliz>KJ!39^*-4{|WFO33VSiQS`AK=g1jh6IT-a;o|QvO}uQY7Ui@s7rnw45SL>B6R#jrU>!3d&UYT7Nb}3?n)cx94cCI^X*ts&@50Tf5Nf8&~9hnj=mVJ=S{P33YNnY6+KT72hA{O5rmqJi@kKmw=r<HU6o-9@D;UMOe8|%Hnoz&M~wbB9&qa6!Z+cm9+I4eLu3X{4>S|?B9{Ux!H~%kcrTT*t!#nP<_U!iWgr-^i^(M)X2JoX5hyEnvcp^{xpUxfb&@rC;k*qvd9xr5!J5rFAg(p8aZ`vHuyO=LK(RWz07^+EPjXmg&1J55m+?65MqR`jYVS~@opu<&%ZulU(Ing*LBVavr<7nFwrKzbA<{u<eqW%<(XKKd_rIy`?48bu@O*$NSVHB+hLb1_EXl@Dp&~6>i_(Ttytd{X#xh>D*Cxhp>>IEas6AFxIY>!a@j;V9KC9Y~3Atvjgw|N`<4yBzQ0b7bJNORp7z**T*=Lq|hlZ0|w<o4h691NDES3tT4-TlOC3nbHC)3KMO=X!s;vg6gt{>j-Z(vIrs`|Xuvo&jquwDQUN6*Bv#2wsj5?qnU0`{Ukb}+#<F(hntG;0gW$7}K6qfg6>M=FB%6UHhD#Vf?4;sF*D_yu~B*Mz9XaG}!UCGKm8Q?U_Oa!3_hiGY-7A_@44S-|P3ycut$>Y_~}EU20I=M}AzbW6*yjeXwg5at7Cdn(f-auBrp4GNs=vP%pRhQW=XL=;oWtTX8Z;~>oj7$w@XgO;q1<zDG7T`YAU^9=#n=)7^CL!`zS^9`(@GHX@mD7vrq<;UZjb8}3g6Pa4^@g*n$aDPf1yrf?~Thqs<Pp3b8L+FX_IlR%t(ty|=Mxks9jo?67E|hUW9z9W&O_M4E`PjJKvA#iU6E-Dt8(=`hEhqA2ahLSF&lIRb(Fo-BHrz?b9el4*AoU4!ZO<K?r-5l3F6#|xLi|C&bwGB936nt#1Z|4=vN_jV!Zhqtl4l}D0t}O5j+nmQNo{0T5wvb+DLG%|;(^%1`ZE1D567;FgZqN7sMY5bi;DBiLO_aQR+yfM(nj+?*X&&`pR0P1v0WIfxnk(5uNus7acn^)UF3Tbq>U%x(!h-_Mt@DoAK9;+bPgg4SZF7hot75&a!|uuHbk1~ZN&j*J88i~O8Z(3GnBY49NjZ{%DyBRUtdk2?gOG@(JgOT3A%l|6$Q=(4)H<zfK&c^NviImYFVs^II5HWDy&03=;FxdZca;zX~~O;>4~@043T+BUnccd13yUd+Lj7gl?i46KETp=EbQpZ(gO#3K*{YKd`7$b_>JwU2o)#U0}r*pI2p;VaL2A7VYWUO+8a3-BrAtzdE=yq&DXn3Q4q`&j%X!Av`}VLpkZwrjsu{g#(Bl2hv;@>UE!HjYS|mBJ2Nod3Xx#a6qutCtyBR;D?o1_00sX{jY1i&YLH{~oiDUyM&3W^SUp52qVKjEa;nnrI;d(=JU!(;b)<QfMchAe16+<dXl{!BL?INB87t*HJv9=h!$h-K&TcYJi96s}?a^QobVQR%9W4kEfvqVEV}SN!_P4iUGK=h*0=UtY+d|nKoL2X`qw19@sN2i3ni({q*+r=yJ~Ptb%dn1xNH0lBg!-@8*9<E+Mqyy&icWCcNQd(Xd8d{MJzM6Aj2im)yyXq+*>aaTC9B`vdnkW34-D3jh-+A>G^Zl~L~qFMvCxd2?jvu~5F@%I4%@OYw6QK270_aUx#kq&>5VQ<_s++_0HMtul?Yq2O+|B4NG)MJbJS-v<EC<dv{ZU}%KnZBt7D(8OSg1eGF`hL1xMzetjO)u)-AnhlmVA7WbuXBY;BO&bhe!J0xa}c?fN+fW5*p{ZQSv07Gi}Jd(DEf_Iqn4R!xUCDP$qEuvmiNodW$g)r@DX)s5=d%?k8r6Y!9H=gB-HU$@7?CLD<)B2cWh(`~Ue>nb&@X3Q(yHT})Fz=k^FQkWvkP}a^|l$J*efC{E_#>?Ov2b=}Q@5qj=RQz&$<^%#adIP5g#Z0rK1E-|0Kw5x-EWpn_(bJba>s^2Q7H_VwplFQVi>OMe0aKM?v<n|Yn(j6;a|T#@;^n}9e)G4Yg&6sefs`$J>Sh+0V2g4C6&*(BQ5nsk(SYPl$Agk}`RiEWGMqJ4FT2xIihwnWS?N5nsP0FHweqg2TM!4MP+|jj%9ck{Gk3~o!&gdsjoExrVhI%!El4R@kk@(|LNC;S)I>%1A<ZZ{4c(-YSOJB{ydPSHY_VOJr_YyTzy`uX*M<SQQ!Tv_X?|8MR`oa8gsu>}3O%qw=R01>X(W*C_6BOcpl4PBlUFhp3~(ZFQYO$RcXbD5lPZ!fvpYANf}$=_mm{-!cPvOY;_e!iBKU#Ek8GCLPGbb0lv^wL4F_Nt%DS48V5PQ4oDAZWXu6j<4bmA?amq)zz;M;gqw*hy48~yR7m%`M5Xv5hGyl%vUI;n$a}@e}J8?Ga=c1wf?ku-8CW}wjh6t=G`r9{;{7Kr=sd&rez)0oaA1d-^7-B|?`0?5o9j6D5qWfz-oR$t46X_93QVL&hJV`%5HZukas_G3*IW9EAV1k~q3^%ac3RkZnjp<WwX(qx;CTICK_}b|l9E@?QT$AG=ftSq7EQj*zWIwFEV-q^ev_WZWo?gNRuR-Xf!-g;)pMF-jz&6-gyrlEJ<;WF1rXfO>uYA?jr^w!U(@}XSqrt>Rd||N12YQ?6G5BkzPTH|B*u%bb))#sXTTJ;=gtxs;`hwg=y2W+KEbcN6XPAnYS>=U-^VE~#k?Q14vbgK_^`QMqYEsOdj7G_pBOm2ecxz5UR;%L(p^@b8@qr3Wzn=dybq}`A^U^YYv?sIV1MJCj64P<|3F8B4V?+n-i*VVTJ1TEh>tq?%fikP}^S|x}%RkXKu)DqnNsPsp&%4?3yUQnDUE+D8TV7%R;pwOKmkSi+_4R*ETX)(%|B+2xRAhL~8l1AVy2ekppu3gg<R!)7;_H{^xv8TvzFg$pPw)Ty?&~{vI=m#97hnJK<9`3MmHasK7QS3b9Zbs~mjX2g+&y3RdDz*$`lnytfB50ApI_;xU!zUJcX<O4DqnGF&$GW6&g$xsrIIv^eI4^T0j?+K${jH3d2@LitDCK2d)G&m!-&B&uIAhW^VA1L-fe&+zrM7*>iTwX5CHGaBaHJmbu>U3CcGZl^K&(AtN-<8qw^@#R_4ea1yNsNdY5yJIiC38Ju%RA;JSbpr4!?Uk9x6&Te|w-1@9{;rBd~#He>PEK24}Qbz_7AmOA&ls^#+rxYQ1XrChtJ&z4MaS`KprmUSj8*6woh!IbN#h1$_^4~w6bDa)PGTn7RR{2}mFLk2rN$$N@L>&(FnC7~qtBhIuY?WR1&uU-O7CK$Pb>~M6H4D+t_%`hQ832?y``l4R-B?}dJhRE${`xg;I(K>WNBiJ_?CRo5j#{$*g93CxmRsE~bblv0;7lb*T(`Cq(3YbRcDkFCCpLZx_snhL{L<u_rmZ>vCk~uEpLfepV9;chal#_Yv>d3nx7j#<VrIXnU#MpecA|HD~Q;2CP7#SR`HJ@{=Glgo*n9RH)Ujw}`>~T+iixFl=gtNd%YZ@%}+{P9VA;nyB$OlapxU(y*leoq3Min`qGFC5c(iY~=8E(GKH{LwmLOVPPcEMD(-gqD6`QtDRf>b35Fw>{#I2X5b^v|L<u^YlJS9+%F#%Xg7gh|)6mHHewOKr8d4AqWuE(J|fRSF6D0k48SNKHzl!_G3gbvD_&u6A?r#TNuaN_#x815-w+(`E%ZO>Rf9cJzQ)jg6PiTsDe}Z!ziPrSrKfdMvl@jVzd7Xo+DsE)D-LXPVZYUfl;-dOVXo5Erq3bVJ_<V15+nF?s?(_&2a$(3#u{3ab9y@_CX(!SNc@0weMk{cO7K7jDRVyZU}1OVDXbONqrvcJ!*d02rrrqUY7PxZi5TRCn<b%b+!3M8&e?a38FJN<oD*wC{G!eGrg{QdK64Q_K>q#YM)#&t4l|!A<s)IfacqE6&f#ZZ(Wyb8IBNDnbuVuB-Mc?Fm=-2&!3j^s}{{6b6~*lv_S{;8!l!pW_ZcYiK4*m(xxNaPN2ht7FJH*$XRW`8Vwu*z>Wrm2JM1{!;Dz`Zs0#HQ82+0drEwW^d$X*J8$lnxYX!GEF^sT9mqw6Hjw_kapN;jmHR$#rfsq?bKr_yc^9$uW_M}BaqX2I&?2=JEb$j-wNfS+6*OkXcaW+D+O5yeKdjrqe|lv+SA0lLcdqOO*X=0ZYhSStA^PsLm_)0`aN=bYvee+QYuG%aWYHSo&pUD8KI>MG~^}8Q+;aRqUh#ql2p=7#k2F!!dc=a>yS({C=mN>HCeh9V<~09^g@s9q<BmDoADOC@un=7)X>ZD6JiCndIk9yq!dT8KnXm8W+j&Gt~P|H#Fo~}-##BeKO{`m+g_Wl?Xl2ZgXsFi23M;OPS6%m8S$#9sa|LZOKxq$cT@fax?w1sC@sl!PN(FX<G29fhzc$ACvJ_UhlUgZ_wk!JP@@4#2l|5>056I>ka`Ol8D8vIq-j)Y0Ev?tR}$rvP`dHurDxPQr3xsaKp(Vp_?(gf5nCi0i(?rCR9cRZjdiFe0emV`+?^tea?M!BrB0rp*GZIUp}NzKz?)If^fT&86DA8V{g_@{!Qk7n2;CBvFSLp78X8koV?LXI)}ne82F5tE&oE5&H<kct3b_EG1#Nann804u33ey)y#4JYccBV232Mja5*D|X#?(!AE=~?CGZZx3umK+ysuXx=Oz2~TCk(X4VuQ38NDm`X;@y-Ay=*UOkIfF-FP%)}JJuBK-j3=^6f(21qye0xOg923#FIc(V3YroYXMJ#VX_iZ9N!rtr(SeX`<ZSiv`trLw`aSKC$$G7oiVl?xX4GdZwQM6p^Fsz3D3MrMB&S=Fm8`@nFb|a(tO?(XGg6UXz8v9%bNjAD=}avd`e3?PytcCgibyydhz6&R-;i`-*bTNz0P;!L~<ULb+zw>%60=&hXC2+$VKZ?0TkO2=g{g{uNKCnk-PASPS7;=<kYfZ6DGB3)#rAoAh=bT9VhZ1hx4-f9;;yFiT8eAju;-yzcFnGSc?Iy4(8f1TuWbE_N#?SraLFJjhe3_<}Ijtq`s(hmJe1>y?xEzOMUfL0<BjY**J%0eeI;Hp;p3{+vvpUI!3BaE?b+XNV(3m$Xo-D$B}|7)sln+))reCWMAOLi9AImD41zyel<ol&>XQm&RlK`c3{@#nIUVo2uyT85RgSw0ckjxwgaARZV_g|{8U!3A?Jb51B*9s8z81Dcs6a!4J6EF*-dnp^}1MaSC}S-3Gka|`t2fX8<dDQ+58~p^Xk!N^fm5Il21;l6cw$R$z*nYs?P1PFIdzJTdPCd*08X(V02#p&NBG*<vpX2)?o+PEj_d77I(dPap`Z0p$^IEX7xE39D9%C9iwqfvVgbPSz;TChE@@%t<~ywR~qGKhsoV}8!X_}Kh;Ys7HpN4k9p9RXt51jBJdDE5EOml9L7{ckcNCwp>H&5?>1+~e5|Vk4>IU*-j;Z{QEyKAlezRIX#If!${&cdce=IL8ohcJiW2hsYR)xb)&U51+{v*cFRjDtf#8}g11090Xx0*feDJAE4b(VFN>I}!qZybv+SL?*gF)0(sFlD~z~XM*>W|Hot{3ITp9T$LG0=947K^2dIFzuP-1t3%>nV#6#2gHRbAriG@RzleG590X15t{RNkdZF@qIWJ<-;V=FxI#z&ssv;)MkIS-A+I}rt4+}!?Oy%RrD<Rz>2rL?}%vQ=+*9S2O8$Mk1-I#!!vX@h+B3)#Q=T~d^TfHAoPIqJ0Ke-)FOD9ntPbZu6}uJujA5Ejsf;aH>!8pXU4khj1RbW_;$ciA(T^oSdNa6`p4jB41wVYfiaH(+zyE0X32A&&Uxvddk5wio{pEl$17{gH{YyX{X>?Ve!XKN(-EG-!c$-V2lQP=t6e$Yta<#)<u==NvUW};84M1s8UBbQAFEQ2#v|U8^dL}Ti@!(WOGGY3n4F#=?>f*m+1wa8(eTI<Nw`<9b3JkVX$@H#s}C}Ijz|DSb}H#6t4ZrPNBA^f5>>x{dioi+=fx|HXsjbbk)WP1s$b`2fn$e>brNuEG%<!29C{-}2f)N6Hx|qw<S}OF&tnE8dPb`NS!?wWEM0RRt;8bd@&Ff&sT~|NbYazT;&;p>Aaamq7mU{U95k1>oRHEW4~Y<28D^eLU@Rwfw7pb!-Eu+$a24wsVV#VLttd7Ca^Wz9;0z^v*jo&szqx7fpdTmaZMeT%moV+K3$X4{6RW^8{Zj2uK__Xt2l%hRBkY$^NFeKIXX28N{m8Ny#j5lKCjz!*RC?Y!g-355m*@SR0x2gm<b>Sl|0!e$aUF;saDObQXUe)mGIUPkNT8a~dumk?iTE+qn`xMTo{KDrJb(qD)|)ar3d@*5FrbD560<ccmo~W1b(dPaS1;LtXR!c2cKP{jgp3dLPf|o#3`@Z@ttO5+U|yjPB6LsM(Ob<jI?VHsLXDUF*TKmqds-pJVCs9k@7u^u!)WSE?~Cp6Hn4IOHKLVFg;-y{<s$=A(7PqiW4k*RL=l+u19&4~m}-?mlusRAOWAcQ7Ni@z3&rS4eoK_sRi?I*Sp@GS+|p*J%DuHCgtg0SStb}8J3!PjUA=}WaxYxWBWIx0&y2OQNK-c65Fof}{(L5^<?$Q9S}cizT_HI@SP-miwXngvTHOPbDQfJDMrmDOclT-eyg|PJ8?FN6#@pFHEI{#>81HRSG=2S_ZBPw+aVu!~T}i!)5$`F*q5!;yrW~zly|y+IvW`a6I?Qd`Du9PcVZSU6q6~|^DTUDSyX&H?THJPMWyh#rro7rxekKmb0B`XO%vhgi+s14kyef9rmY4G2^aK=M&|5k<l$LnL%*uH%RIvR90Zp;f$LX-Iau9*fW_zG`o9LuQWj+qG_#OT8%IuMhApm+4GC!ErLaG5Azu@ePw}@jz*}qmhHrtF+;y&LZYd`=ohJsB`?Ht7@3q)$5(<-!9JfBQO@LO-9xaA(#!5_bII5&vmuNTD|O%^OnB#G)qmFB=ea^NM8@H$xXLSm6}oU3&EW|<o$$faNALPW<-5!$blL+x^hu1QB{`Fq%>lO_0?d3^a=ob)_~o|&xmE{D%-my6%I(PqiQ8{AcNG8v4677J5{y%~oJ4lMu*Akd~&xl{915#k_DID^U*@(@F6YRnfm;%PJ6-x0||8Bo;ZRx2<wU%RK~2P})yqNDv4rlu*^$H{pFi*CjYO*!=f>yGDWQt`o_m64<|Jl0tM-Z>JbR(36I&itF$7*!rYsFxgNZ9x4=1c$s0=_J_I=b=cCJBCcyoqXubme988MW2P1Q<-wzw=W?Af0wJ<@+u+XA=wmY6oX#}+_ml{`&=v97~%EW=MsSg#Vre-GIg@9Oj!pnL4YDN=t5$8?s8UcSAPtJEb?HtmDE8gCSl%pB+9+cGNTM*hxcG48JN@poz0jyi5wX<r{}4u^>xGmyo(a<T@vyF@L(X&td`=v0ii>Q1u!5o`3Ki%(BH}E9riPe84EVNAJKrz3<0hD9N3oR;=uz-I#;2`3yEX^2ZQM$5vwd@#LP?`mWmj)zk<0Hq!d_dRv<bx(eS7eqs@ZwI>=R2@QfIr<s2bv94)pXH4+y0fC#Rjn4P86hBLJ^Ai~%U6QW%-yjEVDt&Tj?Hf0-3HThKEi!|_Tf)Su}K2@Djz*Uer>p@-!Bbb_^l~gvsI97}A80=F%eV#xo!f;eCZyRck3e%HOyiE?ZIrJ$-;fw?Q8yA0rE|EY9Qc5OMt6QI;Dfb!2;M<H)zNv5`W2PafKIY-*uJ)zY$g3mlt!D#@Pq7*fi;DtD+5leB&T9;yMl?vH6IJypUQc#q?+Wo_1OE!MD0KKPb4QmCQgB0<yxr*R+IcLH1M@|MMoZn<)DhR1*eF|s4i$;feP}wWX`WEDCVTYe>%WX77IVFK$%2LmW8VM}h=^6gqK(R+cr;8~&f5>~|1sYNiEYwsOpnV<gP6-P6S`L4U<pd7lG@}<)|Q+p>j_|vx@Z*4#{j2mRLpx8%-XSj49{wohV0h%*xA<DT8q|v(0QF&SVLXgh<7SB<sc8)0X$`=R;BpQva~7fwoCB^a|%;n6iJyIO&2cau`uGY0mlzh4K@&2mvUAQ$!Jx}KA<}0irGMdz!<CBB}jDC$rR3@1?smjTUJ8B0G}83`fp#qXUPnymu(U>c|5(6tasJbm^fOhOIMH~el53}=y;lUNUsxJ^A!5tRHGpu;)^6KGH;7+s|XOm=2ZFJJ-T_<onEZI&%+glW+}Lpc@nx7X4Y?wmp!G_qM2<ndfj#jjFo+%hl|~*F%};vq514${|L8w9Tyb#g>M6KKYj#HyMcGzIKLI%GFHavzYBK{hFG17j^`YkM03FvZ}JL(Bf3q`c~U9MHsWYtb|27@uA`Q26s<azQV~QDjP@SC*S*l?h(vP{@Q`T=d0*$9N6hts+?l4`Sd-AAhw+lSc)W1;p1rnEE|UGS2_j;ZD0xU%H7RQ(NChHi_I$JZN=I1MnuTfkHCvDt!^`udU2a0Lus5<a1YsVSWfFD!3Ej9bIQTgVuP<i<y5fwmgBD$T^3^gS>626DTD*hUrhuy~HmK>Aa39nPRhsIA<<C+8DoG7Q>usz8Heeg{0NM<Wup}7#Vi8t9mQfq6sooqXA~(K;8XIl$9SITvOJOqoVcx%$df5&L@Q<J@Jk&}7lyP5p5LVizgYoehg<QR*W6fZuqB;`Kvax3EvMG$+*tyVOilM`4H?2aQkq?YQC``Ocg~x1V+@klpj2#4h+`zC`aIYdcMEq^HQb9Pq%uO$pK>H=|5t=z5F0~+{R2`98wHb559fqTm)-lqtW;G1s!A55bZD*8-+BEaP650vhDh%<H*^=NY2b3l0<m#a^6+JALS1DIS6e2>#7IJmsVYV(|;XM;zaqBOeoZ!0M=UW!$o8Ui|2EtTv(DN-B5bajOHRGnHDbZxri7zxx^cb%q%}52lJCzB_CN;$LbcVeU(6aFnRYD?sR}-HYd%?DDAyeOARFo)8Su8nx*^2NMP?jw8^(Uw{M7|B<jM>f6X*d`j{BA;{zcJj&?>q4klfEp_&(j?iwLyg2I|_fiHTwFsGb5tXB$YI_I@3e?(eeH&WgHE!ak6$-q+kxu#}#0wA5b#)pQ-}B9u896H-QFq&Q4ZTk~Jy@U+Dl@75<(IEvi7mZxws#MnvDS?E^wLB?(>}gmKy*$8N50r{Ilf?gcYlnK9piH(j*5C>f!R1aXLz#36tI4Qo5(kQ1R*SP(}YqY`9@4d#$a$BY55`codg087IFmVYTUtb+L%E&(&eeUM5gdL)3jp02}j)jFCG$!*<kG{XzPbrLF`^sev0bf5>@6&{Fb97yt4>$A|jT0i~B%Mz^X5-bd)&nUyMI|D4jlK~k^5p2+w?t&8u6YP}NeKHHBy{0W<^<jO^;kek}U8p|@oD_!TAb^jFTvEVm$oAjT_9xx1bf!oy_R$wHT)fe(+A~S@jTId{?dZ#)gi3r|P%O0tRfW1unrReMZus~+BLA!uLTCcH!Rx6gdzuNEi#Bo1d<-TDZH|+vHB1SEq+?pg_Q4`;lmt>pd1h>^ypYUTHPREZ!RKv-uomcqK8k@_>XILQkq*x4AZA+$m}qEC>Oom#$xG!u#*cjMsFiXFhB8ANq0{C|#YsJ6N>Y2PxnT{h0nB4!twb41fu=J=C-QE-Hlhf#9HYb0Bq^S{wIe%56&8_t^ObCLzNgsI4%(;6HY38&-WMlKwGG>OJKsb!*)h5$eg;~ZNelq!GGdr4$1`b}1Q@J9`ztOObC8Buo4^h$BEdfQSY4^0!<Co_%4T!g4y{J%Dh!E>muei^VxpS(ibhG@c!d*V;?(9tY&9r>^{L}@dq*OT!?bD)k_<f|Z5W7)lA?j%FP)$INyg$zwH+ti8Cz^MpDRD*5eY!4_a+~EQ+P<I4@??|;$=kBJ%4mi40CoJWmn#3g`_S^*_q9ou!bx^knsqXN-8M>!CaQa$84^3$}(@z;LB@}E!=0-t4w`XJmI3E1tkgDkYfZL?dyvtwM`sg7S#=gONDNRhEg)DY*G*}xYld4B)lQe9*j#@K|;h8M+sxVeW)avPVDDO?*X;&;6yD4RcbOhnu215H>X8am8O%ZAnqNJ313(5;yyDf<Z%mEmGpQF;lOAFK7%snF<D92`bb>8PIKZ&nQY~ijNI6y1u#|XxorBy?#!y;TIXRHKM4G!j=<xA3^7=FR*xClrAHH3qkU6lAKLZF?;i~?IvQF<?Ob9|7@3S!V^=GA;OJ>gSq@S`lc^Ip;o&t1WqT~JWr$ZKWd~XLtCF5%7R?lsS&D;5VrgOFPG4s#J#H$PDR-Lrj1}yQp>HFRFs(3v(pe<7Rhs^z<y@t*q@<0mr93xITwH^aeveu#kZog1!}<ca8#j)8b8TFU4M{saGFWR4lj#NhF)Ix_8?p|JG<f!hNBX@QuB<G?_ebuOt>N6xg0pZ=eEtxllwF}(f_AY~ahQdeGi{dmg;pb*Jlj!<1uCXnfKNJys73XjZp!W_COxXjOiZ)vI#iFgptagfYrDpIkxUd<lrG5xjjseQ^KEuc>S>+SS3yC#qy;JI#CRZOC24)QUq#}GGtQDnY+#FF;euED`s{@eKR=wrLw1h<CVd7&eUuaDjhBSNX{qZQpJF5xV+DO$r6E7cddfZsm4tH+g~Nf;gJ|wzhOiO}&#VS#LN%o=>~WWLbj}O<RIu9Xcy;j57*WbG;u2ydHI6ujH8i0~PtOu2#+IXHDlTfHi?52~T~3~f9KGS{*>bgLbEJ5m3@9>9)z*<|(RsI;vd$k?$|V<WaZxKQ5w3VcQ&~bcj}<wW)w#`8YPgnzjb16`oxSGbbT_W((3cX-;I2+X+Zql|Dv*qpRPqXtqJ2_(uv^VE(pIz=Ev-LMUzyhC`;`9<;n~vr?1j0c8m|g~UfoZ$^7)ELnV?!BSB?T$6tY4!=xMXn2lX<!{z?{0!GKX1H*{5RkEP;#vX2N;cWQ=|jM&K|vSdL#FSu?LNZeA(H><^buDhI5wW`dc%;$13sa2*pB6^~n5N<`$<7UE*>xFm#6yr~Mlc?dUee|9V-Y!W?YopkcBwe4Ypz|hQl>a#ce?rAR`al%6;mMSX1D@q=cBrBNEv~b8^Rz-i72oR(L>qQ8s|VvFc@!3~GwolwFc~%l>BSNuU&dXHKi4B`<4*kUL{^H;{=ZUJ=B7kxavCes*@vv3KZ^cs8CtTd=&cNcMW(2x7&HNp7N%;b@_`vqI}>Cn?H}Y|WR;NF;}W|^setI=WDE%sXXI4%1!RX*oz)yFDN&dFIv7Y5%0=k-iA)jVZ}*H9Oe{vP;@y=t%sEuF;^y12qM%uzO8$gneWBgXz8!rrTF;wi-xMr|Cn|cLAP$;g&>{#m8y9=&j&Eb&Zo4YO6yPgrwU|hR#%*dPhmRQjaXjGE!-a3cQ#~X(3x~)IoE~T<>P0RERDvOsCGcJ<Wn0+-rOgux8OlH~U>B21KFovzLL*RC?qr9#QgY|O;p!x7^1^u=aPnqB8iF;ObwFHeT;rw?GhpQihJa#qb^(-<N}lAf%9_hu@h;<W+Ksx1HPqgrL_6&;fR`7~6QfDEJA#7SkWVSWI&9Mb3PPlV()_+am7`r{KJI^0-Pt>x6XE#)Q?P`}iw!4H8d#Ezp+ZGkv=*ferFd=4IgDkzYOhU<-Pku^El_)`sB(~!vf_g#g?v`E9}{xTTnVkQ;>Vlj+n~}RUw7~w;4u{9XS2^N^$rauw{A~Np(Oq-$yh8EN*^3hPfPBQtxl$uOPk6vf5bsB9$Y`X-`~KNG*tC@t7mK06k)vp9*&-gWr;hu-6Xgokp=8Ud+cC>ZDL5+>S)#$l#kcq!AGB#8IM#1?<b5^5{g%dN5umyCh!aNB(Dikjp0J2$4lJT5T{}zuH=v^wh{p;(L@sP6|;cTQ+YGqO4UW1Mp#fY@y{z-CFz!yVH^9r)gjCW&h}KMN8})A_Zt*A*JYO&A`F8YL5V1)l38cc3C2O14KPZyX9q1=AIrVcUAkE6KIR(&ve9|tK8Hw+G3FasKV{ac&QWw<?aPnHH|OS<LMJk{;^RwD0^t6XICx3Fe72^KPoGYI_=eCE-E(-OiKPLtJ&Z!x6dJ*Suv{qPf;@VnDw`%%2J*3SyJLNW*d}aB<~G29h+9tN%i=EScb_RxhoTY4?QOV|kURKZqd@8t=-Qq;I8Ou9HeA*l(uDYfg6n|n4ihGW7zo-F@nv(aw}fffrzForj06}a#~d+zy_4F=t|DmN&Qfx|%Ebe*hxKLpZyt_a69@MNUs0>iDHavynT3E9#jG$r5v7ghf3DfPTs~LzAY;2QSaZeDRbMrj;o{hWO1jARBuE=i!li*5U5x&kl0ULvJLw!m6tK`vFgq<R?&Y9{xon6u)7y#z%y!a(hm`iU8fGYQT{yaD@|1l^FuuN;K-~vK$D&)_vJ!Orb}I^;3moEu_5r8-_mWiIMb)xc5ph%}{Z&|pe9*;_&)uAs6w{Iy6VnrKsTm^klD<sptp<LO;<YUmvMLkI0(^j_@mSc=m!$^|_JESxIrxlr_wgIsQxPgovIib&fpIdDUEz*hLBec(F0?mtFi2Jo&GN=c51X%dnW7+=DIC#ChG?P8s6fNoHXH{)MUC@{O%KuS$hyKasnoJJR(ED#x)mb9q$w~*BU-5fidKN$J^%{-nHq&MT-6}Q>N{U(%Z$8#(y@AoP(<HtHRM#K-*r&cq<DJDed<W_DvP*(;s&@JbI{xr{fR;-A~ROXd3tIjOoxePv7FsxoDz4yvD%}-B<P4Hl{#7wA_7}e7RCVW$Lw!!#bg%QH3e{^E4PKRIXJEEbw|}JQ&6{;Wi>NsLbHofJ$z=Q!Ixnj3z1%ulnC`-v9B3cZj8df$Q7O7xRDO$5%Nwg6MDAH6&W@3?|I7`*0bd<b4pgfyZ2E3Y91J@AraTGQfW>{0Epg@-D9B{JKaa#q#;IhNgTFiVQ6DrFe;$M0CUYL#M2vHobH{EfdN9BJt`5lW}AxUrjS~~c;=|jXvR(D{%EQ6^pyP_5mv`OU6*d@wq&|?KMIb_KUtC6sjXXj(<lQjU&!JMv)S4pujy<#>jhZovD)=>4#ti<yxO?q-7LfkEB2ZNW$pLYOstv?ZBocWXkoDg!8--|Z>ky3SgRY=v6~g>(I(&_`OcGhM!s&3g-tjTM?|1lZKvB}Yt~h2Sk0JMx@-EIae)nW#HBDrmZ7YjxhO4<7627Y=Zu%ZHx4)pjNg$RTdDZv_{<3eZuACD3yPU$M+Z(xVS%&&16hEdd!nZ=dDgrB_ATCAVL{Oty%$lHQUj(c#b_5khBV!6X66jA_QcD9|NQ1}MGG<VAp<E}^wiBPFu@k(1}Zv?&Z9D#L8Af5n~n!1>+;vJ!euyXs$O=drxXEe6tmKKVo}|X4r}FIRkt7xMxn$8?vyQ$re^Mx&xWs*_8PPKqQnv^CR&hEvLLVZG=yHL0jY_K?n9bUbQ-!zC9whuk9j||3fW@2E>E8?$AArlg{}<)bf;Q+Bhvh=TCD1CvI$)wbQOAFh0b@plG8{a+wBe1d_m8w1SYR!EEwQK;G|5TPwwgt%qCSNU1oP~HU&jpqAo{f_3l`ZY{cC)Dn;-EjUU-8ubsvSJ}I|W@*57oFqCyQCBaH<k2o2`DbaK<a~h;Grs9;3a)IHhn@8n83>l2U&MzQk%^;LL4rl(I!@Ur4>gOo*_jclJ*3U&l`Q2G=YfKiOtPK%ZRrI%S9{H2Br&IBk$$^o|zduyu&oIP{7V+b?FFH;S97XrndN?f|FecI?l%y2C-guIJfNW+A6jaq4nsQudhQS0qWf^W@xfQNnK^oJi-qK8jmrTy`Z}7F#IXD>ORJkU{Ljo_Emst+w*U5fZd&eepm}!I3);zt04PJxLNrw$#K0f`daDi>GwRlPAd&`k4dQ3xvEMNJmt51==^QNQnP)37^jrhV~j}P=V(PQw}PMx%4VX%jN>8vmG9JZM9rwDI*o%98{i*$?YkXhVi9L_KmFSE)E1?Q<J#Us_pn`Cj<@9RPPmDHq|I~k3VEk{1etMJyGf~;1@5ke!$-{S)nntnb1XX+koo#&-x{Af>R$p_ez=Om`%^b^Jh(#D7m+85!nId@dvtk%ggt^;LO=jVUj4VHhRZ(w(Q4U!m(FQ0d_<#(4)yt>5mMz_4e{=?Hx>n|55$m{F>nzrt=9gqJX6!1MQ')).decode())
for _actions in ACTIONS:
 _actions[0]["market"]=[["BUY_PRODUCT","WHEAT",BUY_WHEAT]]
 _actions[1]["market"][0]=["SELL","WHEAT",SELL_WHEAT]
def agent(observation,configuration):
 p=int(observation.get("player",0)); step=min(int(observation.get("step",0)),719); action=copy.deepcopy(ACTIONS[p][step]); farms=observation.get("farms") or []; hands=(farms[p].get("hands") or []) if p<len(farms) else []; action["hands"]=(action.get("hands") or [])[:len(hands)]; return action
act=agent

```

## G4 base/reactive agent available in this branch

### Source: `kaggriculture_meta_lab/agents/variants/agent_v10_reactive_subin.py`

```py
"""V10 research kernel for bounded evolution from the V7 control.

TOP10 Subin-inspired opening, labor, herd, and opponent-response components are
available as explicit parameters, but their bundled transplant lost its first
closed-loop ablations. Shipped defaults therefore fail closed to the V7 control
rather than claiming to recover the private original agent. Evolution may alter
only the explicitly bounded numeric genes below.

Base history: Kaggriculture v7 phased candidate: mixed premium crops and livestock.

v1 (all wheat) verified the machinery: hired hands run daily watering-first
sweeps of their plan chunks, the farmer harvests/plants overflow, land NE+SW
is bought when the current area fills, wheat is harvested at age 3, and the
SE quadrant is never bought (its $4k cannot pay back late in the season).
Local results: ~20.0k vs passive / ~19.2k self-play (720-turn episodes).

v2 adds a second crop (CARROT) that uses the same 4-day, 3-unit rhythm as
wheat.  Wheat's price curve is log-shaped above equilibrium so it can absorb
unlimited supply without crashing, whereas carrot (sqrt above) crashes once
the market is flooded - but carrot also pays 35 base vs wheat's 25 and its
price *rises* when the town drains it and nobody supplies it.

The town's demand is fully public: every unlocked shop instance consumes a
fixed number of units per day of the products it demands.  We therefore size
the carrot belt to (a share of) the current town carrot demand, cap it as a
fraction of the plan, and only plant carrots while their market price still
justifies the more expensive seed.  Cells are assigned a crop by their rank
in the canonical plan (carrots get the lowest ranks); because a crop switch
only happens when a cell is replanted after harvest, the assignment adapts
smoothly as shops unlock.

v3 added a compact goose subsystem learned from public-match telemetry. V3.1
then retained home-grown wheat as feed and fixed overcommitted market queues.
V4 generalizes the machinery and selects five cows: dedicated hands build
pastures, carry animals and feed wheat from the shed, then harvest milk, CARE
for the next yield, and collect daily fertilizer. Across 18 real replay action
streams cow5 averaged 55.3k with 16 wins, versus 40.5k/9 wins for goose5.

Everything stays deterministic and stateless; ``act`` is a pure function of
the observation plus the module constants below (tunable for offline sweeps).

Entry points: ``act`` / ``agent`` (Kaggle simulator loads ``main.py`` and
calls ``act``; local ``env.run`` calls either).
"""

from __future__ import annotations

from typing import Any

# Crops we can run.  Both are one-time crops with the same age-3 rhythm:
#   WHEAT  seed 10, base 25, 3u/4 tile-days
#   CARROT seed 20, base 35, 3u/4 tile-days (same watering needs)
SUPPORTED = ("WHEAT", "CARROT", "MELON", "STRAWBERRY")
SEED_COST = {"WHEAT": 10, "CARROT": 20, "MELON": 80, "STRAWBERRY": 100}
# First harvestable age per crop.  Wheat/carrot are picked at 3 units on age 3
# (watered through the bonus window); melon pays 6 units on age 10.
HARVEST_AGE_BY_CROP = {"WHEAT": 3, "CARROT": 3, "MELON": 10, "STRAWBERRY": 10}

QUAD_ORDER = ("NW", "NE", "SW", "SE")
LAND_COST = {"NE": 1000, "SW": 2000, "SE": 4000}
# Cumulative daily cost of hiring 1..10 hands (fib 1,1,2,3,5,8,13,21,34,55).
FIB_SUM = (1, 2, 4, 7, 12, 20, 33, 54, 88, 143)
FIB_COST = (1, 1, 2, 3, 5, 8, 13, 21, 34, 55)
# Keep enough liquid cash for the next day's hands and market volatility.
OPERATING_RESERVE = 300

# Hands roughly sustain ~10 cells/day each (water + tour + occasional
# harvest/replant); we also count the farmer as one waterer.
CELLS_PER_HAND = 10
HANDS_EXTRA = 1
HANDS_MAX = 12
# Replay-driven V6 controls. Defaults retain the selected V5 behavior; Actions
# sweeps change one family at a time before any interaction profile is built.
HAND_TASK_MODE = "WATER_FIRST"
# Unlike the rejected fully-global router, idle stealing preserves each hand's
# deterministic zone and crosses a boundary only when that zone has no work.
IDLE_WORK_STEAL = False
LATE_CROP_HAND_BONUS = 0
# Optional replay-derived staffing curves. AUTO retains capacity-based hiring.
LABOR_MODE = "AUTO"
LABOR_PROFILE = 0  # 0=AUTO control, 1=current-TOP10 Renoir-like schedule

# Never queue more than this many market orders per turn.
MAX_MARKET_ORDERS = 10

# Selling below this would mean a crashed market.
SELL_PRICE_FLOOR = 1
# Liquidate everything late: inventory has zero terminal value.
ENDGAME_SELL_DAY = 27
# Empty means sell whenever stock reaches the shed. Non-empty tuples allow
# measured batching immediately after town-consumption ticks.
SALE_HOURS: tuple[int, ...] = ()

# Land purchase triggers.
LAND_NE_MIN_PLANTED = 3       # unlock early for pasture/field throughput
LAND_SW_MIN_PLANTED = 30      # measured best over all public replay streams
LAND_SW_MAX_DAY = 18          # late purchases cannot pay back
LAND_RESERVE = 700            # cash kept after the purchase for seeds+wages
SELL_BUY = False              # SE quadrant purchase disabled (see module docs)
# Across 32 public replay streams, day-8/day-10 timed expansion improved the
# finalist from 93,615.0 to 94,409.0 without losing a game.
LAND_MODE = "TIMED"
LAND_NE_BUY_DAY = 8
LAND_SW_BUY_DAY = 10

# Carrot belt sizing: cells = clamp(share of town carrot demand that we want
# to serve, 0..CARROT_MAX_FRAC * plan).  CARROT_KAPPA tunes how aggressively
# we chase the town's carrot consumption.
CARROT_KAPPA = 0.70
CARROT_MAX_FRAC = 0.40
# Only plant carrots while their price is at least this multiple of the wheat
# price (carrot seed is twice as expensive).
CARROT_MIN_PRICE_RATIO = 1.15

# Product demand per day for one shop instance (6 ticks/day; single-product
# shops consume 2x per tick).
TICKS_PER_DAY = 6.0
CARROT_SHOP_MULT = {"PET_CAFE": 2, "FARMERS_MARKET": 1}

# Carrot production per cell per day at the age-3 rhythm (3 units / 4 days).
CARROT_UNITS_PER_CELL_DAY = 0.75

# Melon cells (explicit NW coordinates).  Melon needs ~11 tile-days per crop
# (6 units); town-center melon demand is 1/day regardless of shop draws, so a
# couple of melon cells earn far more per tile-day than wheat/carrot while the
# market is anywhere near equilibrium.  Number of cells = len(MELON_CELLS).
MELON_CELLS = [(0, 0), (1, 0), (2, 0), (3, 0), (0, 1), (1, 1)]
# Conditional scale-up can react to a visible melon-heavy opponent without
# paying the large-melon penalty in every market. Disabled by default.
OPPONENT_MELON_THRESHOLD = 4
OPPONENT_MELON_CELLS = [
    (0, 0), (1, 0), (2, 0), (3, 0),
    (0, 1), (1, 1), (2, 1), (3, 1),
    (0, 2), (1, 2),
]
# Melon needs 10 days to mature; a plant started after this day cannot be
# harvested before the season ends.
MELON_LAST_PLANT_DAY = 18
# A validated V6.1 experiment can rotate the startup melon block into the
# strawberry target after its first harvest, reusing capital-intensive land.
ROTATE_MELONS_TO_STRAWBERRIES = False
# V5 reserves premium ongoing crops in deterministic rank bands. These are
# deliberately profile constants so Actions can sweep broad economies.
STRAWBERRY_TARGET = 0
STRAWBERRY_START_DAY = 5
STRAWBERRY_LAST_PLANT_DAY = 13
# Explicit phased estate observed in Renoir's 172k match. Locked coordinates
# activate after land purchase; early NW cells start the crop before expansion.
STRAWBERRY_CELLS = [
    (1, 0), (2, 0), (1, 1), (0, 2), (0, 3),
    (5, 0), (6, 0), (7, 0), (5, 1), (6, 1), (7, 1), (8, 1),
    (7, 2), (8, 2), (9, 2), (7, 3), (8, 3), (9, 3), (8, 4), (9, 4),
    (1, 5), (2, 5), (3, 5), (4, 5), (1, 6), (2, 6), (3, 6), (4, 6),
    (2, 7), (3, 7), (4, 7), (3, 8), (4, 8),
]
FERTILIZER_RESERVE = 0
FERTILIZE_PREMIUM_ONLY = True

# v4 defaults to five cows; GH matrix jobs can switch the same logistics
# machinery to geese or sheep for controlled comparisons.
ANIMAL_KIND = "COW"
BASE_COW_TARGET = 8
BASE_SHEEP_TARGET = 6
BASE_GOOSE_TARGET = 0
ANIMAL_TARGET = 14  # compatibility: sum of ANIMAL_TARGETS is authoritative
ANIMAL_TARGETS = {
    "COW": BASE_COW_TARGET,
    "SHEEP": BASE_SHEEP_TARGET,
    "GOOSE": BASE_GOOSE_TARGET,
}
ANIMAL_COST = {"GOOSE": 300, "COW": 400, "SHEEP": 500}
ANIMAL_STRUCTURE = {"GOOSE": "COOP", "COW": "PASTURE", "SHEEP": "PASTURE"}
ANIMAL_BUILD_OP = {"GOOSE": "BUILD_COOP", "COW": "BUILD_PASTURE", "SHEEP": "BUILD_PASTURE"}
# Ordered compact capacity around all four shed entrances. Locked coordinates
# activate naturally after land purchase; only the first ANIMAL_TARGET matter.
ANIMAL_CELLS = [
    (4, 4), (4, 3), (3, 4), (4, 2), (2, 4), (4, 1),
    (5, 4), (5, 3), (6, 4), (5, 2),
    (4, 5), (3, 5), (4, 6), (2, 5),
    (5, 1), (6, 3), (7, 4),
    (1, 5), (3, 6), (4, 7),
]
ANIMAL_KIND_SEQUENCE = []
ANIMAL_ACTIVE_BY_DAY = {}
EARLY_ANIMAL_SLOTS = 999
ANIMAL_EXPANSION_DAY = 0
ANIMALS_PER_WORKER = 3
ANIMAL_BUY_BATCH = 3
PREMIUM_SEED_BATCH = 8
FEED_STOCK_DAYS = 3
ADAPT_OPPONENT_MODE = 0  # fail-closed until an evolved profile clears gates
ADAPT_SHEEP_THRESHOLD = 4
ADAPT_COW_TARGET = 8
# Optional mirror response to a cow-heavy opponent. Disabled in V5; V6 sweeps
# test whether moving exposure from milk to wool helps in the shared market.
ADAPT_COW_THRESHOLD = 4
ADAPT_COW_RESPONSE_COWS = 4
ADAPT_COW_RESPONSE_SHEEP = 6
# Service ordering is sweepable. Feeding first is safer; harvesting first
# reduces held-cap losses. Both are measured rather than assumed.
ANIMAL_SERVICE_MODE = "HARVEST_FEED_CARE_FERT"


def _plan_cells(unlocked: list[str], board: int) -> list[tuple[int, int]]:
    """Canonical row-major cell list over the unlocked quadrants."""
    cells: list[tuple[int, int]] = []
    half = board // 2
    for q in QUAD_ORDER:
        if q not in unlocked:
            continue
        y0 = half if q in ("SW", "SE") else 0
        y1 = half if q in ("NW", "NE") else board
        x0 = half if q in ("NE", "SE") else 0
        x1 = half if q in ("NW", "SW") else board
        for y in range(y0, y1):
            for x in range(x0, x1):
                cells.append((x, y))
    return cells


def _walk(fx: int, fy: int, tx: int, ty: int) -> str:
    """One deterministic step toward (tx, ty)."""
    if fx < tx:
        return "EAST"
    if fx > tx:
        return "WEST"
    if fy < ty:
        return "SOUTH"
    if fy > ty:
        return "NORTH"
    return "PASS"


def _near(cells: list[tuple[int, int]], fx: int, fy: int) -> tuple[int, int] | None:
    """Nearest cell by Manhattan distance; ties by canonical order."""
    if not cells:
        return None
    return min(cells, key=lambda c: (abs(c[0] - fx) + abs(c[1] - fy), c[1], c[0]))


class FarmerPlanner:
    """Deterministic, stateless planner shared by farmer and hired hands.

    No episode memory: every decision is a pure function of the observation
    (plan = currently unlocked quadrants, crop = cell rank + town demand).
    """

    def decide(self, obs: dict[str, Any]) -> dict[str, Any]:
        player = obs["player"]
        me = obs["farms"][player]
        private = obs["private"]
        tiles = me["tiles"]
        board = len(tiles)
        # Stable cell-to-species mapping. Cows come first for earlier milk ROI;
        # sheep add independent wool demand and reduce single-market exposure.
        # A very sheep-heavy visible opponent is the one measured failure of
        # the mixed profile: shared wool supply crashes both sellers. Because
        # cows are bought first in batches, switch to eight cows before buying
        # sheep once that strategy is observable on the board.
        animal_targets = dict(ANIMAL_TARGETS)
        opponent_tiles = obs["farms"][1 - player]["tiles"]
        opponent_sheep = sum(
            isinstance(t, dict) and t.get("animal") == "SHEEP"
            for row in opponent_tiles for t in row
        )
        opponent_cows = sum(
            isinstance(t, dict) and t.get("animal") == "COW"
            for row in opponent_tiles for t in row
        )
        opponent_melons = sum(
            isinstance(t, dict) and t.get("crop") == "MELON"
            for row in opponent_tiles for t in row
        )
        melon_cells = (
            OPPONENT_MELON_CELLS
            if ADAPT_OPPONENT_MODE and opponent_melons >= OPPONENT_MELON_THRESHOLD
            else MELON_CELLS
        )
        if (ADAPT_OPPONENT_MODE and opponent_sheep >= ADAPT_SHEEP_THRESHOLD
                and animal_targets.get("SHEEP", 0) > 0):
            animal_targets = {
                "COW": max(ADAPT_COW_TARGET, animal_targets.get("COW", 0)),
                "SHEEP": 2,
                "GOOSE": animal_targets.get("GOOSE", 0),
            }
        elif ADAPT_OPPONENT_MODE and opponent_cows >= ADAPT_COW_THRESHOLD:
            animal_targets = {
                "COW": ADAPT_COW_RESPONSE_COWS,
                "SHEEP": ADAPT_COW_RESPONSE_SHEEP,
                "GOOSE": animal_targets.get("GOOSE", 0),
            }

        step = int(obs.get("step", 0))
        day = obs.get("day", step // 24)
        hour = obs.get("hour", step % 24)
        animal_specs: list[tuple[tuple[int, int], str]] = []
        if ANIMAL_KIND_SEQUENCE:
            remaining = dict(animal_targets)
            for cell, kind in zip(ANIMAL_CELLS, ANIMAL_KIND_SEQUENCE):
                if remaining.get(kind, 0) > 0:
                    animal_specs.append((cell, kind))
                    remaining[kind] -= 1
        else:
            for kind in ("COW", "SHEEP", "GOOSE"):
                animal_specs.extend((cell, kind) for cell in ANIMAL_CELLS[len(animal_specs):len(animal_specs) + animal_targets.get(kind, 0)])
        if ANIMAL_ACTIVE_BY_DAY:
            active_slots = max(
                (count for start_day, count in ANIMAL_ACTIVE_BY_DAY.items() if day >= int(start_day)),
                default=0,
            )
        else:
            active_slots = len(animal_specs) if day >= ANIMAL_EXPANSION_DAY else min(EARLY_ANIMAL_SLOTS, len(animal_specs))
        active_specs = animal_specs[:min(active_slots, len(animal_specs))]
        animal_plan = [cell for cell, _ in active_specs]
        kind_at = dict(active_specs)
        service_animal_plan = [c for c in animal_plan if tiles[c[1]][c[0]] != "LOCKED"]
        money = me["money"]
        unlocked = list(me.get("unlocked_quadrants", ["NW"]))
        hands_now = me.get("hands", []) or []
        seeds = private.get("seeds", {}) or {}
        shed = private.get("shed", {}) or {}
        inventories = private.get("inventories", []) or []
        prices = (obs.get("market", {}) or {}).get("prices", {}) or {}
        shops = (obs.get("town", {}) or {}).get("unlocked_shops", []) or []

        # Animal structures are permanent reservations and never enter the
        # crop conveyor.
        plan = [c for c in _plan_cells(unlocked, board) if c not in animal_plan]
        plan_set = set(plan)
        rank_map = {cell: i for i, cell in enumerate(plan)}

        # ---- crop layout ----------------------------------------------------
        carrot_demand_per_day = sum(
            TICKS_PER_DAY * CARROT_SHOP_MULT.get(s, 0) for s in shops
        )
        carrot_cells_max = min(len(plan), int(len(plan) * CARROT_MAX_FRAC))
        carrot_target = min(
            carrot_cells_max,
            int(CARROT_KAPPA * carrot_demand_per_day / CARROT_UNITS_PER_CELL_DAY),
        )
        # Replant gate: carrot only while its price still beats wheat clearly.
        wp = int(prices.get("WHEAT", 0) or 0)
        cp = int(prices.get("CARROT", 0) or 0)
        carrot_ok = cp >= max(SELL_PRICE_FLOOR, CARROT_MIN_PRICE_RATIO * max(wp, 1))

        def _crop_of_cell(x: int, y: int, rank: int | None) -> str:
            melon_cell = (x, y) in melon_cells
            if melon_cell and day <= MELON_LAST_PLANT_DAY:
                return "MELON"
            # Ongoing strawberries produce four premium harvests. In rotation
            # profiles, the first-harvest melon block counts toward the total
            # strawberry target instead of creating a second disjoint block.
            strawberry_time = STRAWBERRY_START_DAY <= day <= STRAWBERRY_LAST_PLANT_DAY
            if melon_cell and ROTATE_MELONS_TO_STRAWBERRIES and strawberry_time:
                return "STRAWBERRY"
            if strawberry_time and STRAWBERRY_CELLS:
                if (x, y) in STRAWBERRY_CELLS[:STRAWBERRY_TARGET]:
                    return "STRAWBERRY"
            elif rank is not None and strawberry_time:
                rotated = len(melon_cells) if ROTATE_MELONS_TO_STRAWBERRIES else 0
                premium_rank = rank - len(melon_cells)
                if 0 <= premium_rank < max(0, STRAWBERRY_TARGET - rotated):
                    return "STRAWBERRY"
            if rank is not None and carrot_ok and rank < carrot_target + len(melon_cells) + STRAWBERRY_TARGET:
                return "CARROT"
            return "WHEAT"

        def _rank_of(x: int, y: int) -> int | None:
            return rank_map.get((x, y))

        # ---- single board scan: collect what every unit needs -------------
        mature: list[tuple[int, int]] = []      # plants at/over harvest age
        urgent: list[tuple[int, int]] = []      # unwatered, will die tonight
        unwatered: list[tuple[int, int]] = []   # any unwatered supported plant
        fertilizable: list[tuple[int, int]] = []
        empty_cells: dict[str, list[tuple[int, int]]] = {c: [] for c in SUPPORTED}
        weeds: list[tuple[int, int]] = []
        animal_cells: list[tuple[int, int]] = []
        animal_cells_by_kind: dict[str, list[tuple[int, int]]] = {k: [] for k in animal_targets}
        empty_structures: list[tuple[int, int]] = []
        unbuilt_animal_cells: list[tuple[int, int]] = []
        planted_per_crop = {c: 0 for c in SUPPORTED}
        for y in range(board):
            for x in range(board):
                t = tiles[y][x]
                cell = (x, y)
                if isinstance(t, str):
                    continue
                if t is None:
                    if cell in animal_plan:
                        unbuilt_animal_cells.append(cell)
                    elif cell in plan_set:
                        r = _rank_of(x, y)
                        crop = _crop_of_cell(x, y, r)
                        empty_cells[crop].append(cell)
                    continue
                if t.get("kind") == "WEED":
                    weeds.append(cell)
                    continue
                desired_kind = kind_at.get(cell)
                if desired_kind and t.get("kind") == ANIMAL_STRUCTURE[desired_kind]:
                    if t.get("animal") == desired_kind:
                        animal_cells.append(cell)
                        animal_cells_by_kind[desired_kind].append(cell)
                    elif not t.get("animal"):
                        empty_structures.append(cell)
                    continue
                crop = t.get("crop")
                if t.get("kind") != "PLANT" or crop not in SUPPORTED:
                    continue
                planted_per_crop[crop] += 1
                age = day - t["planted_day"]
                if age < 0 or t.get("yield_units", 0) <= 0:
                    continue
                if not t.get("watered_today"):
                    unwatered.append((x, y))
                    if t.get("consecutive_unwatered", 0) >= 1:
                        urgent.append((x, y))
                if (
                    int(t.get("fertilized_until_day", -1)) < day
                    and (not FERTILIZE_PREMIUM_ONLY or crop in ("MELON", "STRAWBERRY"))
                ):
                    fertilizable.append((x, y))
                if age >= HARVEST_AGE_BY_CROP.get(crop, HARVEST_AGE_BY_CROP["WHEAT"]):
                    mature.append((x, y))

        # ---- market orders -------------------------------------------------
        orders: list[list[Any]] = []
        shed_value = 0
        # Different products have independent price curves, but high-value
        # stock goes first so the ten-order cap cannot strand it.
        sale_items = sorted(
            shed,
            key=lambda item: (-int(prices.get(item, 0) or 0), item),
        )
        for item in sale_items:
            if len(orders) >= MAX_MARKET_ORDERS:
                break
            if day < ENDGAME_SELL_DAY and SALE_HOURS and hour not in SALE_HOURS:
                continue
            qty = shed[item]
            if qty <= 0:
                continue
            # Never sell tomorrow's animal feed only to buy it back from a
            # scarcity market. Strong online opponents aggressively consume
            # market wheat, making that round trip both fragile and costly.
            sell_qty = qty
            if day < ENDGAME_SELL_DAY and item == "WHEAT":
                feed_reserve = sum(animal_targets.values()) * FEED_STOCK_DAYS
                sell_qty = max(0, qty - feed_reserve)
            elif day < ENDGAME_SELL_DAY and item == "FERTILIZER":
                # Fertilizer is worth more when converted into extra premium
                # harvest than as a raw sale only in fertilizing profiles.
                sell_qty = max(0, qty - FERTILIZER_RESERVE)
            if sell_qty <= 0:
                continue
            price = int(prices.get(item, 0) or 0)
            if price >= (1 if day >= ENDGAME_SELL_DAY else SELL_PRICE_FLOOR):
                orders.append(["SELL", item, sell_qty])
                shed_value += sell_qty * max(price, 1)

        est_money = money + shed_value
        # Purchases in one market queue are processed sequentially. Track the
        # remaining cash instead of checking every order against the same
        # pre-order balance (which used to overcommit the opening bankroll).
        available_money = est_money

        # Land: AUTO uses measured fill thresholds. TIMED reproduces the
        # industrial opponents that unlock NE and SW in rapid succession even
        # while premium fields are still being converted.
        if len(unlocked) < len(QUAD_ORDER):
            nxt = QUAD_ORDER[len(unlocked)]
            cost = LAND_COST[nxt]
            ok = False
            if LAND_MODE == "TIMED":
                if nxt == "NE":
                    ok = day >= LAND_NE_BUY_DAY
                elif nxt == "SW":
                    ok = day >= LAND_SW_BUY_DAY
                elif nxt == "SE":
                    ok = SELL_BUY
            elif hour == 0:
                if nxt == "NE":
                    ok = sum(planted_per_crop.values()) >= LAND_NE_MIN_PLANTED
                elif nxt == "SW":
                    ok = sum(planted_per_crop.values()) >= LAND_SW_MIN_PLANTED and day <= LAND_SW_MAX_DAY
                elif nxt == "SE":
                    ok = SELL_BUY
            if ok and available_money >= cost + LAND_RESERVE:
                orders.append(["BUY_LAND"])
                available_money -= cost

        # Hands: stage livestock setup instead of assigning nearly the whole
        # opening workforce to structures for animals we cannot yet afford.
        present_animals = len(animal_cells) + sum(
            int(shed.get(k, 0)) + sum(int(inv.get(k, 0)) for inv in inventories)
            for k in animal_targets
        )
        active_animal_capacity = min(len(service_animal_plan), max(2, present_animals + ANIMAL_BUY_BATCH))
        animal_workers_target = (
            active_animal_capacity + ANIMALS_PER_WORKER - 1
        ) // ANIMALS_PER_WORKER
        crop_workers_target = max(2, (len(plan) + CELLS_PER_HAND - 1) // CELLS_PER_HAND + HANDS_EXTRA)
        if "SW" in unlocked:
            crop_workers_target += LATE_CROP_HAND_BONUS
        h_target = min(HANDS_MAX, crop_workers_target + animal_workers_target)
        if LABOR_MODE == "DMITRI":
            if day <= 7:
                h_target = 3
            elif day <= 9:
                h_target = 6
            elif day == 10:
                h_target = 7
            elif day == 18:
                h_target = 11
            elif day <= 27:
                h_target = 10
            else:
                h_target = 3
        elif LABOR_MODE == "INDUSTRIAL":
            h_target = 5 if day <= 6 else (8 if day <= 9 else (12 if day <= 27 else 4))
        elif LABOR_MODE == "CHAMPION":
            h_target = 12 if day <= 27 else 4
        elif LABOR_MODE == "RENOIR" or LABOR_PROFILE == 1:
            schedule = {
                0: 5, 1: 3, 2: 4, 3: 5, 4: 4, 5: 4,
                6: 8, 7: 8, 8: 9, 9: 9, 10: 11, 11: 11,
                12: 9, 13: 10, 14: 10, 15: 11, 16: 12,
                25: 11,
            }
            h_target = [
                value for start_day, value in sorted(schedule.items()) if day >= start_day
            ][-1]
        h_target = min(HANDS_MAX, h_target)
        to_hire = max(0, h_target - len(hands_now))
        hires_today = int(me.get("hires_today", len(hands_now)) or 0)
        for h in range(to_hire):
            hire_index = hires_today + h
            if hire_index >= len(FIB_COST) or len(orders) >= MAX_MARKET_ORDERS:
                break
            hire_cost = FIB_COST[hire_index]
            if available_money >= hire_cost + OPERATING_RESERVE:
                orders.append(["HIRE"])
                available_money -= hire_cost
            else:
                break

        # Fund the long-lived premium crop before livestock can consume the
        # whole opening bankroll. Generic seed purchasing below skips it.
        if STRAWBERRY_TARGET > 0:
            have_strawberry = int(seeds.get("STRAWBERRY", 0))
            need_strawberry = min(
                PREMIUM_SEED_BATCH,
                max(0, len(empty_cells["STRAWBERRY"]) + 2 - have_strawberry),
            )
            cost_strawberry = need_strawberry * SEED_COST["STRAWBERRY"]
            if (
                need_strawberry > 0
                and available_money >= cost_strawberry + OPERATING_RESERVE
                and len(orders) < MAX_MARKET_ORDERS
            ):
                orders.append(["BUY_SEED", "STRAWBERRY", need_strawberry])
                available_money -= cost_strawberry

        # Buy each species independently. Sequential accounting prevents a
        # mixed herd from promising the same cash to cows and sheep.
        animal_owned = 0
        animal_buy_budget = ANIMAL_BUY_BATCH
        for kind in ("COW", "SHEEP", "GOOSE"):
            target = min(
                animal_targets.get(kind, 0),
                sum(kind_at[c] == kind for c in service_animal_plan),
            )
            carried = sum(int(inv.get(kind, 0)) for inv in inventories)
            owned = len(animal_cells_by_kind.get(kind, [])) + int(shed.get(kind, 0)) + carried
            animal_owned += owned
            missing = max(0, target - owned)
            affordable = max(0, int((available_money - OPERATING_RESERVE) // ANIMAL_COST[kind]))
            buy_n = min(missing, affordable, animal_buy_budget)
            if buy_n > 0 and day <= 18 and len(orders) < MAX_MARKET_ORDERS:
                orders.append(["BUY_ANIMAL", kind, buy_n])
                available_money -= buy_n * ANIMAL_COST[kind]
                animal_owned += buy_n
                animal_buy_budget -= buy_n

        # Feed is ordinary WHEAT product in the shed, separate from seeds.
        carried_wheat = sum(int(inv.get("WHEAT", 0)) for inv in inventories)
        feed_stock = int(shed.get("WHEAT", 0)) + carried_wheat
        feed_target = max(1, animal_owned) * FEED_STOCK_DAYS
        buy_feed = min(20, max(0, feed_target - feed_stock))
        wheat_price = int(prices.get("WHEAT", 25) or 25)
        feed_cost = buy_feed * wheat_price
        if (
            buy_feed > 0
            and available_money >= feed_cost + OPERATING_RESERVE
            and len(orders) < MAX_MARKET_ORDERS
        ):
            orders.append(["BUY_PRODUCT", "WHEAT", buy_feed])
            available_money -= feed_cost

        # Seeds per crop: enough for every planned empty cell plus a reserve.
        for crop in SUPPORTED:
            if crop == "STRAWBERRY":
                continue
            have = int(seeds.get(crop, 0))
            seed_need = len(empty_cells[crop]) + 4
            buy_n = min(seed_need - have, 25)
            seed_cost = buy_n * SEED_COST[crop]
            if (
                buy_n > 0
                and available_money >= seed_cost + OPERATING_RESERVE
                and len(orders) < MAX_MARKET_ORDERS
            ):
                orders.append(["BUY_SEED", crop, buy_n])
                available_money -= seed_cost

        # ---- decide ops for every unit --------------------------------------
        # Cap on simultaneous plants and per-crop seed budget (the engine drops
        # ALL plant ops of a crop if requests exceed that crop's seeds).
        waterers = 1 + len(hands_now)
        plant_cap = min(len(plan), waterers * CELLS_PER_HAND)
        plants_total = sum(planted_per_crop.values())
        plants_assigned = {c: 0 for c in SUPPORTED}
        def _plant_ok(crop: str) -> bool:
            if plants_total + sum(plants_assigned.values()) >= plant_cap:
                return False
            if plants_assigned[crop] >= int(seeds.get(crop, 0)):
                return False
            if hour > 22:
                return False
            return True

        def _standing_op(
            tile: Any,
            zone_set: set[tuple[int, int]],
            fx: int,
            fy: int,
            inventory: dict[str, int],
        ) -> list[str] | None:
            """Action on the tile we stand on, or None if nothing to do here."""
            if isinstance(tile, dict) and tile.get("kind") == "WEED":
                return ["DIG"]
            if isinstance(tile, dict) and tile.get("kind") == "PLANT" and tile.get("crop") in SUPPORTED:
                age = day - tile["planted_day"]
                yld = tile.get("yield_units", 0)
                hage = HARVEST_AGE_BY_CROP.get(tile["crop"], HARVEST_AGE_BY_CROP["WHEAT"])
                if (fx, fy) in fertilizable and int(inventory.get("FERTILIZER", 0)) > 0:
                    return ["FERTILIZE"]
                if age >= hage and yld > 0:
                    if age == hage and not tile.get("watered_today"):
                        # Watering on the first harvestable day adds a unit.
                        return ["WATER"]
                    return ["HARVEST"]
                if not tile.get("watered_today"):
                    return ["WATER"]
                return None
            if tile is None and (fx, fy) in zone_set:
                r = _rank_of(fx, fy)
                crop = _crop_of_cell(fx, fy, r)
                if _plant_ok(crop):
                    plants_assigned[crop] += 1
                    return ["PLANT", crop]
            return None

        def _animal_op(
            fx: int,
            fy: int,
            zone: list[tuple[int, int]],
            inventory: dict[str, int],
        ) -> list[Any]:
            """Build, stock and service one compact mixed-species chunk."""
            zone_set = set(zone)
            cell = (fx, fy)
            tile = tiles[fy][fx]
            wheat_carried = int(inventory.get("WHEAT", 0))
            desired_here = kind_at.get(cell)

            if cell in zone_set:
                if isinstance(tile, dict) and tile.get("kind") == "WEED":
                    return ["DIG"]
                if desired_here and isinstance(tile, dict) and tile.get("kind") == "PLANT":
                    age = day - tile["planted_day"]
                    if age >= HARVEST_AGE_BY_CROP.get(tile.get("crop"), 3) and tile.get("yield_units", 0) > 0:
                        return ["HARVEST"]
                    if not tile.get("watered_today"):
                        return ["WATER"]
                if tile is None and desired_here:
                    return [ANIMAL_BUILD_OP[desired_here]]
                if desired_here and isinstance(tile, dict) and tile.get("kind") == ANIMAL_STRUCTURE[desired_here]:
                    if not tile.get("animal"):
                        if int(inventory.get(desired_here, 0)) > 0:
                            return ["PLACE", desired_here, 1]
                    elif tile.get("animal") == desired_here:
                        available = {
                            "HARVEST": tile.get("yield_units", 0) > 0,
                            "FEED": not tile.get("fed_today") and wheat_carried > 0,
                            "CARE": not tile.get("cared_today"),
                            "COLLECT_FERTILIZER": tile.get("fertilizer_available"),
                        }
                        modes = {
                            "HARVEST_FEED_CARE_FERT": ("HARVEST", "FEED", "CARE", "COLLECT_FERTILIZER"),
                            "FEED_HARVEST_FERT_CARE": ("FEED", "HARVEST", "COLLECT_FERTILIZER", "CARE"),
                            "FEED_FERT_HARVEST_CARE": ("FEED", "COLLECT_FERTILIZER", "HARVEST", "CARE"),
                            "FEED_CARE_HARVEST_FERT": ("FEED", "CARE", "HARVEST", "COLLECT_FERTILIZER"),
                        }
                        for op in modes.get(ANIMAL_SERVICE_MODE, modes["HARVEST_FEED_CARE_FERT"]):
                            if available[op]:
                                return [op]

            zone_empty_structures = [c for c in empty_structures if c in zone_set]
            zone_unbuilt = [c for c in unbuilt_animal_cells if c in zone_set]
            zone_animals = [c for c in animal_cells if c in zone_set]

            # Carry the correct purchased species to its reserved structure.
            if zone_empty_structures:
                target = _near(zone_empty_structures, fx, fy)
                target_kind = kind_at[target]
                if int(inventory.get(target_kind, 0)) <= 0 and int(shed.get(target_kind, 0)) > 0:
                    if cell == (4, 4):
                        return ["PICKUP", target_kind, 1]
                    return [_walk(fx, fy, 4, 4)]
                if int(inventory.get(target_kind, 0)) > 0:
                    return [_walk(fx, fy, *target)]

            if zone_unbuilt:
                target = _near(zone_unbuilt, fx, fy)
                return [_walk(fx, fy, *target)]

            hungry = [
                c for c in zone_animals
                if not tiles[c[1]][c[0]].get("fed_today")
            ]
            if hungry and wheat_carried <= 0:
                if int(shed.get("WHEAT", 0)) > 0 and cell == (4, 4):
                    return ["PICKUP", "WHEAT", max(2, len(zone_animals) * 2)]
                return [_walk(fx, fy, 4, 4)]

            service = [
                c for c in zone_animals
                if (
                    tiles[c[1]][c[0]].get("yield_units", 0) > 0
                    or not tiles[c[1]][c[0]].get("fed_today")
                    or not tiles[c[1]][c[0]].get("cared_today")
                    or tiles[c[1]][c[0]].get("fertilizer_available")
                )
            ]
            target = _near(service, fx, fy)
            if target is not None:
                move = _walk(fx, fy, *target)
                if move != "PASS":
                    return [move]
            return ["PASS"]

        def _farm_op(
            fx: int,
            fy: int,
            zone: list[tuple[int, int]],
            inventory: dict[str, int],
        ) -> list[str]:
            """Farmer: fertilize premium cells, then harvest/plant."""
            zone_set = set(zone)
            op = _standing_op(tiles[fy][fx], zone_set, fx, fy, inventory)
            if op is not None:
                return op
            z_mature = [c for c in mature if c in zone_set]
            z_plant = [c for crop in SUPPORTED for c in empty_cells[crop] if c in zone_set]
            z_urgent = [c for c in urgent if c in zone_set]
            z_wet = [c for c in unwatered if c in zone_set]
            z_fertilize = [c for c in fertilizable if c in zone_set]
            if z_fertilize and int(inventory.get("FERTILIZER", 0)) <= 0 and int(shed.get("FERTILIZER", 0)) > 0:
                if (fx, fy) == (4, 4):
                    return ["PICKUP", "FERTILIZER", min(FERTILIZER_RESERVE, int(shed["FERTILIZER"]))]
                return [_walk(fx, fy, 4, 4)]
            target = _near(z_fertilize, fx, fy) if int(inventory.get("FERTILIZER", 0)) > 0 else None
            if target is None:
                target = _near(z_mature, fx, fy)
            if target is None:
                target = _near(z_plant, fx, fy)
            if target is None:
                target = _near(z_urgent, fx, fy)
            if target is None:
                target = _near(z_wet, fx, fy)
            if target is None:
                target = _near([c for c in weeds if c in zone_set], fx, fy)
            if target is not None:
                mv = _walk(fx, fy, *target)
                if mv != "PASS":
                    return [mv]
            return ["PASS"]

        def _hand_op(
            fx: int,
            fy: int,
            zone: list[tuple[int, int]],
            inventory: dict[str, int],
        ) -> list[str]:
            """Hand: watering-first daily sweep of its chunk."""
            zone_set = set(zone)
            op = _standing_op(tiles[fy][fx], zone_set, fx, fy, inventory)
            if op is not None:
                return op
            z_urgent = [c for c in urgent if c in zone_set]
            z_wet = [c for c in unwatered if c in zone_set]
            z_mature = [c for c in mature if c in zone_set]
            z_plant = [c for crop in SUPPORTED for c in empty_cells[crop] if c in zone_set]
            task_sets = {
                "WATER_FIRST": (z_urgent, z_wet, z_mature, z_plant),
                "HARVEST_FIRST": (z_mature, z_urgent, z_wet, z_plant),
                "PLANT_FIRST": (z_urgent, z_plant, z_wet, z_mature),
                "VALUE_FIRST": (z_urgent, z_mature, z_plant, z_wet),
            }.get(HAND_TASK_MODE, (z_urgent, z_wet, z_mature, z_plant))
            target = None
            for candidates in task_sets:
                target = _near(candidates, fx, fy)
                if target is not None:
                    break
            if target is None and IDLE_WORK_STEAL:
                # Preserve the local-zone priority above; only genuinely idle
                # hands help the nearest outstanding task elsewhere.
                for candidates in (urgent, unwatered, mature):
                    target = _near(candidates, fx, fy)
                    if target is not None:
                        break
            if target is not None:
                mv = _walk(fx, fy, *target)
                if mv != "PASS":
                    return [mv]
            return ["PASS"]

        farmer_inventory = inventories[0] if inventories else {}
        farmer_op = _farm_op(me["farmer"][0], me["farmer"][1], plan, farmer_inventory)

        hands_ops: list[list[Any]] = []
        n = len(hands_now)
        animal_n = min(n, animal_workers_target)
        crop_n = n - animal_n
        if n:
            for i, (hx, hy) in enumerate(hands_now):
                inventory = inventories[i + 1] if i + 1 < len(inventories) else {}
                if i < animal_n:
                    lo = i * len(service_animal_plan) // animal_n
                    hi = (i + 1) * len(service_animal_plan) // animal_n
                    hands_ops.append(_animal_op(hx, hy, service_animal_plan[lo:hi], inventory))
                else:
                    crop_i = i - animal_n
                    lo = crop_i * len(plan) // max(crop_n, 1)
                    hi = (crop_i + 1) * len(plan) // max(crop_n, 1)
                    hands_ops.append(_hand_op(hx, hy, plan[lo:hi] if plan else [], inventory))

        return {"farmer": farmer_op, "hands": hands_ops, "market": orders}


# Current-TOP10 observed two-turn market bootstrap. The planner still computes
# farmer/hand actions from the live observation; only these market queues are
# fixed. Disable with SUBIN_OPENING_STEPS = 0 for an ablation.
SUBIN_OPENING_STEPS = 0
SUBIN_OPENING = (
    (("BUY_PRODUCT", "WHEAT", 13), ("SELL", "WHEAT", 13),
     ("BUY_PRODUCT", "WHEAT", 13)),
    (("SELL", "WHEAT", 13), ("BUY_PRODUCT", "WHEAT", 5),
     ("HIRE",), ("HIRE",), ("HIRE",), ("HIRE",), ("HIRE",),
     ("BUY_ANIMAL", "COW", 2), ("BUY_ANIMAL", "SHEEP", 2)),
)

# Machine-readable bounded ranges. Evolution tooling may mutate only these
# names; arbitrary source mutation remains forbidden.
EVOLUTION_BOUNDS = {
    "SUBIN_OPENING_STEPS": (0, 2),
    "LABOR_PROFILE": (0, 1),
    "BASE_COW_TARGET": (4, 10),
    "BASE_SHEEP_TARGET": (2, 10),
    "BASE_GOOSE_TARGET": (0, 4),
    "ADAPT_OPPONENT_MODE": (0, 1),
    "OPERATING_RESERVE": (100, 900),
    "HANDS_EXTRA": (0, 3),
    "HANDS_MAX": (8, 14),
    "LAND_NE_BUY_DAY": (4, 10),
    "LAND_SW_BUY_DAY": (7, 15),
    "LAND_RESERVE": (300, 1400),
    "CARROT_KAPPA": (0.2, 1.2),
    "CARROT_MAX_FRAC": (0.1, 0.6),
    "MELON_LAST_PLANT_DAY": (12, 20),
    "STRAWBERRY_TARGET": (0, 20),
    "FERTILIZER_RESERVE": (0, 30),
    "ANIMAL_BUY_BATCH": (1, 5),
    "FEED_STOCK_DAYS": (1, 5),
    "ENDGAME_SELL_DAY": (24, 29),
    "ADAPT_SHEEP_THRESHOLD": (2, 10),
    "ADAPT_COW_THRESHOLD": (2, 10),
}

# ---- engine entry points -------------------------------------------------

def act(observation: dict[str, Any], configuration: dict[str, Any]) -> dict[str, Any]:
    """Kaggle simulation-runner entry point."""
    action = _PLANNER.decide(observation)
    raw_step = observation.get("step")
    if isinstance(raw_step, (int, float)):
        step = int(raw_step)
    else:
        turns_per_day = int(configuration.get("turnsPerDay", 24) or 24)
        step = int(observation.get("day", 0) or 0) * turns_per_day + int(
            observation.get("hour", 0) or 0)
    if 0 <= step < min(SUBIN_OPENING_STEPS, len(SUBIN_OPENING)):
        action["market"] = [list(order) for order in SUBIN_OPENING[step]]
    return action


def agent(observation: dict[str, Any], configuration: dict[str, Any]) -> dict[str, Any]:
    """Alias for local ``env.run([agent, ...])``."""
    return act(observation, configuration)


_PLANNER = FarmerPlanner()

```

## G2 base static tape used by market overlay screening

### Source: `kaggriculture_meta_lab/agents/variants/agent_v10_subin_106845775.py`

```py
"""Static research lead imitating Subin An episode 106845775.

Source: audited current TOP30 snapshot, best-listed submission 56098520.
This is an open-loop exemplar, not the original reactive agent and not approved
for Kaggle submission. Generated actions trim nonexistent hands at runtime.
"""
import base64, copy, json, zlib
_BLOB = 'c-rlKOOG4pw%vcxn1gPT-D+i~BlFtAmEDFUhqy5W;{drqfZ%3ul38&6dn7d<Rkhb%YwcZM%f7HjrYSaA_0{*-kM;QV*Z=q8fBgL)|MBntc=2C;eev__4<BB9+PwImfB)bA{r`M^<MYe^`1?Qp*T4VY&#!-d@wZ?8?YE!bKYsVin~yIxFOEMPUVr}Y?e5d&*B2iS@7^un%Rc_;pPT7#{`C0%;}7|d+TVQl<zIey`~L94eevaMUjOv=$Jbwe;LYRl#bz7c{_w-$@bi~{SX}jo$6w}G{dw@-zWLW*em;HGmoGYv=Jgh*ujZeg-t*#@E+2fll-W;CzK;FY-+p=f?z`VUf8^sYUvAy`v8O?u{n+AL<PE-i{pMiYUwHnDKgGXuJbd{0^~Ial;+9UIbVu#-#mjMzYvIG;@ZINs|MBqd@h31vmgB{*;PXBI^zrg-$vcauqb})oc}eGi1yc$9+WFFsuRk8%FJFBfCNk{*^5sfqzi|EI>o=bV+nTG^Ek4bM+3#MSXg=20&&)@t{LtfUvj#SP=xO{qPk8o4=J;R#Ev~28@1FPJaNnmdnEc*(iv$CI-d(0w5GIuOyJ5WJ<Br3;{CzddyTUND=N*T8@#zuc4xTd`_oq*ne|Q-xJkP*y_0N*=)(edth4BW#z=8wh83&X+(9;E|pDhgN^}C$`1xM1V0bTx7>5IwNEnc)@q4^+Z5vGoF!0`tjqdsAl7Yg5MoY>dPI{lmRE%E%l{O#$VoG*EN_wMlK<8S|Rc>nS3ySM*sxy4<+34X8=@Par#`Ob4>uy`A;yHnCK`RM2Mo+U2fa5=nQKH=+8x(rmE3@wWSv(e>un*21lWoNHBuf~{Mr2D9GgZb}-k?id&*ROe=%LMCp)%9L>ny0xn_-e1a!<xN1S$8YuIr**E`7CRkE~}o+;FB&s;lD1We%f#Lsv;FOcUf|h=Pj+L=s6aTUY2OHgDVRb)w#@mPagWH5X8Pu&I>ZYi?nm~@S+Ndygqw0PXR$`G(niS?rN>+O49k2qq#O@q!%l19+i8+<(|Lrhu81_Yp<R`M)@)eI?0zc+?UH<k;dB3VNxD)l35ueubkc>=$)Mbc`%hfZ*WrVapU2V9jGF~yvM+|w#GD}doZXU%3)<+2&&+xNnt!EG63;9hXf+eTahS)CcAPeLdGJjNn*XKbpq08M4ZT>9ayOTSAVOxuZ{X0R3?fCO!lJp7{HcMIeFul#|yrW#q5yj9g^x<gzQ|^qS0A5pJ}^KmFE=i5udZ=YHd9BrkyK%Tg$Gjc@(e)-t`q3>RvPw0{q2rf)iqFT!QY+nlgoukxx*42zuWQtA?#WXy^YF+c;oEw96u*^?@bIn>zO|;_)={FzN>W!iYcTM-VIuyMAwqUy<K$Kb!O5f<`3ywZ^dzqBi4)I$>OfRVjyccm1%g(8(E9TB7le-xL`cWwnB<OC{JUV#o?v9QwR>(+jQ^U9_=Pl00PX)ttchEz20C5Cqgf8evs=+FiyRL?S$>8XV8YKqTv$bm9|qiqnRf+le8$$K{FAmRfh40JQ)zOTdk6#?GJFlSEBcI+dIqG_Jv9h5&fhie4tETY?`l$~;c*m3^Ok;q@YX;Vwv(GL0TPH$i^qyZ4VjR|6A}0o?VgS-cLqu1((kdAV#_5FhXu7BSvdwT-Vo@kxY>TMV*^VQ#0<2X>M376xxA*<%J32Uj)eE`J<{XnoZ$!!}u`7#U<#1z8>3UACNTveY8y%hxTz6wdbn-0Jn7`D{v7`Q(`X@bUfY<KGVN-~St!+9(H5zqdZI2lorA6QTiEz=_3j=VVa4U_M^)<t)hy#;bd%*9f17^3!KriAKCj_kYT2tb!*zq?(e$ai>qa7oe~jcJnD`Q_<hzPBU<28ym(W4KQ7DKkJZst?soT(UoX%)lMM{2-qo}f|HAI+U2EPpF8Z2NR;&A$}gv+fv+wtvC9{y1)&WL1<<}wTZz+^k%mK?CNMp&%@`qoTaW*y?(-VGK0bc_&%F_bpUcjtKfo6-Awl7QV422~i`q|Eu^tTk!ae=GseGsSsn@@zQAZq!>mx~SQH4U6FG%_Z9Uy%19zvr6bbLsjZ9|})&@tlH*~MG}D8Qu!N%yvShFo+0q{x&bnM@kdtwkf6HAZsW-Sn+EFq9DLgx>Mez%JyVHW;Zn<#ufR%p_hYI0Tkhdm|n}RMH+@1C-xsJ3_KbH5mrp6J3C6i$jlkv8$P>z{bLCu+)!7kT!tD=R3vSG-ckTF*Uln2Eq>HzjTif?ZxCN?ObG~m}kk8VyGLkLMM@AEn#CMN}6x_Se<2Y@Ks@702>4XiFB6R)_ssEp;bOQ+Fh(ax@4E#EJDR?iPNnXXP!tlPEJyCUY%eTi2RGoc$p}vOap1LSzL<j9`?wpQirfKW>_rD(v5%rI79tLGD@Wyb*v&!_LT!adhHZX*Yj{>d+k!7Vh#NZ-OY=SM3$_(SyqfV^JJLiQX4PQ^Wfjf2*xyL8MY27mxB;E9y|GAGYp5w#_Br#7Rk>wBTGSc=4Dz6AYvKDnBC!SE{?4mlG@xFnX|yDp06w)IT>=&a}@n36^7EMeJxLL#)z)Hr!5?@!cy|M*Op|%#$)y6Uc1Qsi?j!pZ=fq$Z2m(Z4vV`%8Yu>+JCS_J7~TH^mtSb}VAVD^m(79MV@pu16NlcjAbq;bj=Gs_xS4)Jx5mYaY~U?^WEb*hARI^%ErQO@WmwDyQ%<7*Sg^Ejwje~CXJYMn;*&F2677bWY>qO%ZkD^UgA4rQW!>Zj-6nj37lx<T3`(?dAWK(qiFnXYUz?JrBlgF)@Ba1F($X-N{24xd&FwaAPu-(z`J#?mYw5&JVQd0|3Ug3GO;eKVADgxBT@7ug;%Zfbj=i(%EiL1jPSG5l&T;v0=r}9b$!2LSa$wy>uo@N+p-M|{rz<-#y9CF1p#NN-AFGM4ffa!^H5ihZgY!hV+_kD>-+gdhybG`$2w_xut)!ZTcXv-JxW7<M5{8W7DST*kvF&<E09vI+X;~fY3{zYU(-wCQZ#09t!OSV}2pCs16hcPL?TCTEj}JrsF8};A)FYH>a~;#g(<9Qs*>l$M9z`ay^<(_wYM~=QDkJJonj*XX)I@sX&R2TIv1{_LK<Yxn;K~{g8s%AVQuGR;Fsc~w{Wop5b>!$YPIIFuF6dzeIU5h{nIs=oJXu_i#x-skfOXk%^u#;Ys>IsV6c8oG#5q2&7-toQ5+G?-Wll=jcSLqXqQID1s0=O^@oe~Nk;h4pm)D&c2d|fCX|aip$(Rzw6xu8Fai($}k_8Qt$2k;u&&4H^X*TPFJs3y^ribJfor+OB?VtjTyF!Xu%1~L0FwZdKZr&Nq*w8F=*t^aXY=CvKf_JkTNqV8J=mmL|dssaY)xKX=Oj=PYqX8e%D~Q3n+_b=`;H{gT-W8;6eU^C8Mg^+@gVQ=7-RVxdJ`{2)%b^9dE2JX1eQcugr(w2v8_sM&vhoh)z4-8Fm2h4r&*l7PVNE^lg9M?hMak!_Wy<2`gm<g4pp}xw??WhD0|g~7*!tmzy>JHn{_*j{K{mN|g}W$ftJ2K$t|9LZ_f=r1_-*b8Y(0KakD=e(3m~<o6jb#z?kgmbFj<vx2l(+J$%};h*(Z^zen9qFyq^O_33Yvh;h1zS4g@N?4B(86wIkC&;i@Kcf|WxZk%8h>VID~=NeJ_#ldao5!jEHI!sHL|!rJqF`7U!mx_)y)%nBDw2MGNE{Su(+Z8D6{-gtX|>n0|v(~AR3k>8=WpYxoK-Q(@H0&PIKE4pe5IA+ZB<@ofb?45NMcwnff;6&b(jR=qUqVwIzdz~SPoKClHCM5gY6J_zu<5G=AhUyVYbQ(Y71iv#AP_9C;xO6^GbL=p{z{y0Gy9XzeS8!X|Qx(vPoKJ@e4sn8N%6fC*5k~P*v+SHFk!~#Y{BRBfyxqbr{<<$-?qo3!DOwcNPt=XE`+2(5S8d>ZoB`+iyl#f9vkYmIfXqg{C7(ua07f088nG#tP(7m<Y^b_rW5m4<Hp3iiBO%XvG>SjCcriw<Lb~2k;jQp*pr@(4>YEn1&WjooQPzjT#xJ6{L=9)Rs!+s8Lnwe{W6`f~aowI%^+=)=Dmoz)n+$q1;T<M=K1!Xd11*(NWNbc9H$-qwYtgS=4q}mnrW_DLPQIH0B86goV=8$)0OeM?VBU<@vaz*DiDHxN;ZDx#aLiORLX4*KRr)e+$Wa7#nnm#`WU2H{I3DZq+NOXXC%z^Ebqu0j5GQgc8MCzV3!@acBU{e}7}919{2%0bDB}mzZhIHg$Ko(f0I07kh&#217Md+m`?h;p8KI`{FweQEu~dL+KVUc{7J()4-03Usd=k*T+_U>gmu*$T3G2D>#leVaYL}PmsV^XA!j$EjAq}rSTY~}ZaUa3LKA0Q8SlYjsQb0+)yN@w{!aU<Q>DtbmLUTY9#WyCax~7A#TbQ}y+(yZKXhu?>>wc8(KzO@O9U42<m1|*A7T8Wr6oJkY8gnKwE~XJwTsgl7V_#k;dBElabyBG823o^vg(!ltDA(=;e=O7ygnTd@hz9DQ4+{PtDzEHoO(!PxO|@_<o?KwX#_$m1KERn`4vz#iC|ogUQu&``2T9VWxzG+O>43*spyESJ<`dHxC{G`d<ili(|K!71;d}<!2Bm35h|F<}p@luEWb8_uz4dH|gCr*t+YGShhZ|rM3Fo;~3EiV;L(J$IcTPoX?=sFm9zt6IQ4n}@g1JL`+p`TN`93o)3RM>j@^BVABeG51#uVTJ<K_actYttA2F0F?8G^FF;Chz%2I>`_zL%07A93xrKc>n*DPv|B%M6hB3?4ldo@nX)f#W#-M!d${p1rmv>?y~(L}r@OkVKbc5r0MGP5p-IK4?8ji*$C~!_W*Jq(eWIL|N6#=SnRB+9dX+^L2qMMzD`vauj9o2}Y|y-G=O{_GLjlMV+G}40K$L?6(#pQuMIkA!JSCW|Yd93kbg_HcyFEA`*T8v<b$-mdGpe-odiayRypD=;7(jrU4Sr5u+J%xeHDq&aZ(NWq}}A^MJPEDF&hh2m)9<yCc@oAK~C7pafNiK&A=JIxUhjG--_AJzplYS&%s@m#3}Q)uvL-_Pp&bEl)ez961+N(3Jk;NO#Js^y!AczMJ%V?9RnvOIjiGr@9?A>LcBaN)-y$a6%RVtwI`8{b(lN;t?K-Pg<Ay7-o!7LwRe0kBmqj*`%+(0%a&lv`fya$~tgJ`Lx^Pi@NumlZ)_}LdTMYo8Pc`8D}-vhEwY4Ry0ZA=OM`$Cf2Wr7cPgzZ>>HjoQv%Ksm2Kr6-i>yd4FRk&rc;Oe`Elu*j8Q_f?k2m=zxl)Ay%f*80KBYxFQd0!4wU7h}Ml$K`eufM2Q-Zs1f3i@~}1yldi&k7U%QSJC2XAzz!mJv1^N5FwzOAalneaF5$S!*0H674E3^fyc`v=^WOmr6>#f|8ydSh6p-FqP$d+4C(vX)GOlYvQ}SB#1U(!Xj*vb$sB+2;&{OgRU<R+t?J3c1^=jZ}=w-CLwP2c6u2~tjX|kE#C|UTD5&<U=Q#}t>_m`8cC@`2lUpDv9M~j|wCd$<Y{`f8otG&c|<%mr+4}qAauWYYX<&w+X(xOtvc6NRGnTKM!Yhn*izak<h+j!t@{f`QH>|S+F58r=(3Mao27&p*ELARPp<}ku5$WC8UvNz6G_rct|CkvR%&du4%LCDYRLt08OX9?$~RuPA0GHqdppskFJIxbI#l!)v#!{t>FPp6pKMyU&0R0})ViU7uT4UP&I%0-C^UHb}ka!0JGUBJFP%rSY<>l}!=xJ_2IE2t$hwqho0GA5Wru#8-xY95|dTp<ck05fSvQCa*6AH98W5C1ro=VJlP9M|y?{QOnJqHZhoPSg4}p9&z!5Jes@a3*t?kjRjOSA15iTr;^-s)p50GC`t7`82$(Oxjl`i7`i8k`&P7)@>)vOo9;$t%!1@?>%$OD}^13NjwL94V3TReh*fZrS#JXSm^R*`Mi`>>k$TRnVI?UxGvygGZF@$!@J<~n*fkM_AI&>6^^hfR~R4_P;5Z08amyIRU2RSRY>KG$B0uEf`{R7tFpm4cL}iD@?dAps|MR)Rf808O%>8sAcuY9bd;mBVnwDIHVegW8a0U;$dsLNEFXqraLq!T`T(gyM8Y#mo%l{}R9OVktAS$UvZ@>!U^n~<7g#{|fbu^$c?yO)M6s_*3y4F5Xf+`z23H+&nyQ|@FiP+Vz_vr8f|1w;j)<3wErSn)QBbP5FeZ5;o2L3#N3)CqiM;9=QmjkcppA9fz}O4yf~a0-%p|x%)z}fFm$-1*JTt6xy9KwSq`Twj)#^Gs!UxUhmbWMIoVK?hF#U9{=-SbW4TV;@BhBR^aXtyF_o6zGbT){1h$i-CWQOT1VSh81__!~MoK$KmF4)CE_)<ihCvF$-rl^U<gq7$wl<w*2>Zd*z^BGs6R<aZy&F6ca&ml?}**mA-eq-;Qu)UsNF!4JT))2W5uK=0OB>uLO)My3Eo^zRKmD`W*y2TmPSU~%%3%xj36WPWrNqVmeLTO}+1?Ex}XhvG`JFI|g41;0}<119^-$$oJGqLCRBj~NMqC+G!grHE984>{f*GkoW!d!R=IFAGg<5;+`v%(RU+sbH(Hh&Dwz+8#TDi;~#{ktSB?_3;fdB9DNeJ=Ge9;C~~$fl0)crU+O#x*ZXH9~Oab$Zl(m#tSEipi!!$;^5z+OKp3u^y(wjEHHS@HuF9M4CZ)260<}Wfr4U=(kmFlaO{-Q_VyU(31dUmac68qNA#-CWD%$JQGG&6g23aG{c%wcw=PS9j%8mRW|1M+@0u3{wssGm?RfLBX-7;I>x#^h?354vMPJp2h4<?mZ|78AzSH)i%ug1d{Sm<No-D7V&84E36`Eyer#++R6w1gO~R$RDXYBHf2c^`kqT8>{GjUeF+x_3%l_GSZ&o}=;UMCl(|Rx$08T4&Mo(&ap2LzsmHAI#X_kP)qP)~zdvS!L3l=eLlbWtd8;==^a6m}>M~Rd<|H-vv4*<w>Qb_^L@w=8V;vxcBdJy!5?%^iq!8flX{f`+sWIF;<VwuUa4rbOVlZNRfX+ie9XnaA?ow$$?UUjdENzzb_Uqa8;mn6Xc5FqL6P=Rq3Y=`ISP1AhFRDg4k79707JBVo^swgVefK^bTEkCPaeNP_16-~=H<fHIpsXa#7v^%8(ZIlOtWN<U%ERp3wgbNW$YeJi8>zoy>3PJvHyq+2_K`=Kgxu<cARujiUm#Q4Vgk#St_)O9!DJoN)vxCmod%7H{?(SIC2Yh90_Os5`C0I^R`<9WQu{sUPji~gxRFCF*WT%O+7Xp&-vG`C-PVbWfoLflMoK;XCJydlVSHM<e<qE}s5RsU+Fl7;`xhV>#I*7i>$g2@599s^EsAJ%73fp8&UNlF~K%#S@^sxzGx{XrFQyb_sE8v|JwrTmqxwtDZ$Y8Rg+5%_jm4UlkB~^*Uofn`5kpld#)fMTQU?3l0&4Bj}bb0EjJTfhnWRPU={;tSX3Z+6r{KHagg3^F~N>gY+=A|$u`-dd=(9?9}O-tO{82;Ld0MyZVjS9AkaLpzk%U~p;w@ynu7`%GMUGWMV%^Zq!Kp1<PwC98hil>KHLW#)44jgy2MsHIi53DNvV}+oY)QbU=%i(V^&R!OpwBjy8dGquU#j49t2$rR=T!SvnIfL9#U>VPk7*YmbBGCd~19_Lse74_JTqNrjBUB&oVE6%%g|${AH~}TIvNNeW6hPHkp?zLLaa<T@>**k*C4{7R`dn&Igz2gdY3a5mt-{=-D2g=XfOD0DT6c*x#Tgz2mC7m{n9}=&2ZMn~NL@_MZdqFE!?D=T!6X+AUKP?&SfebF7o~tYH&4N%U6wm#9ttEE2?L9$k32I4Q=TkJM?se2JIsMpO7dkV4X+Au`|MQ+YWoK>+k4JPVZM!AAH+316nvJlrfK$|r07yAO1@EpnB=r+ieI;xJRS_lipBD#LPE5Y+~`Xx3^Hu%O3W#M)E%UxDvXU2!7b6D;W$&4_H#aBD3LAcyn1uY#He%m#$6ixb<*`_)qr`J^KloxrAdpemmAcuJW~FQ!rzbUP+C^Yy;>fC={AEB$XR}`yGa6XO;W)lmq)STQ0)?iU4HeM*D}5BxmeInYN@A6<_GMuj`2@ngm}gdpl1?s94HX`A1VaeYyw>lJSO{AVWst?7g{<58CFILM;L@c(hew*=NOa`=e`WF>8UW50x2|6<&&QlnY95=QVKFB$Gz@{0`D;ov?G8KRBX9WCfWDpH=rV4otc};0}&CrF3~EdM5^78EKKjI7{V32H)XWhSW!Edq9wWeorcBIZQtkH)Bz><WQ}9!!SmFb@r(Hi+D_{>g_5~n#gQPB2L*VzQ>C66^<*E$ZTs!$J>1lUt6LbjjlM=n+a@;dee@usyKXPBiV2EfuIDl#0-0U9D&>(vSifSgHMO8>m7<E~NK+8N%cN<0yRJIY<=n#oXSNQjRQlatquCJ(;`;p@vaC=yHDI1vmi4Zw_i`rO4H81<YNA$jz)%JjQbEIK9Z*E4!olGaOk6>08g;CSKwU1`ddOya95wwtAPMEZw2)H+O)PvE1g=j9?*Vk2UnBt4Cgd9$RAJM&#>}^W5Fe1<w6izOffNM|YKHyf(~6{qo%2b8$`fh(;+B6bnll-THBR}Sk}<2(5P@6LP#^Ev;WOU2*-EP6IaH%Z@L=w>!*PxZ=6C<~zVzwpDxkQ&HpJpdtf~pj<n&0^$`4hICCH`tq*_adNL6y4QuUXgR<J689;^zI$O*tppgKVW>=bGksWD&4j*tnnkRr@>wSvkbUVUzmP1Tadf`9BJ_rdg_nK=FB;G-glhATqYuD>n;MsRHkg$8;g&~S{vddWA~{w2G@HKnpoCY8o?YC``|JBE4ya#n&U5uQn424J^kU;!Q16(@y^4?DWFcnA>!vxs+w!!{Qf-RGwU0qJ&l_8E}^cF~#UNZyj<u={*dq~tL*)AJIXT+6RM6%wsD$(c4OQvw`T_$aLmU(1I#(9ICB%x>Z-La$J%$_);Ej44(S)PMlnL9e>3rCq4EZe2kLhMQnwAn8S-CV2)_(2;2g-0sQuSnBbeC<#_F<f$WFytID29L8NArXe6D2g8N9*K{`2y=kOMq1tk+&q;K)_ZYSXY%F8Q40@hqS7CzjO<^yoM27gqx$&ZBNJFx*hq>}XqGv%kIkrH%2N2zuEn&7v>-(XzMnjBi8p$0Yl2UA^v#7fP1&1kC;-PLrqZC$MVbXn)gY(J$^{Q|99TqDON5k=eoqZe(;uO;9<uPC#7my-{&8(nC{<P!CT#<<9mLw_!FvK1QAw)=H2t-N%hDxC}O?i%^J5ILTpY(+`sYSPI+MY}-1dq3XMICE`BaV)_O*Ak@T->kkc2@ELLJ?b><>yZoP*E;M+Qvd3J~S-y)U)u@W^3{nbH-LYO<5!9b~Kdf!hj-b=&2xUdy<2-c^#C9+#n@)A?hM#Hg&k(T3Q<E%;X*BeUdyf=)Bp%TuRq$`k4`FyvCf)^bob%_}hyAX1Vzr>zS@ae1WbLCrnN;s9R%Dx{(KR0`K2x4a^wS@bjpG0;Ce{MA|a*3MKoZkuVlm#Q9FS%#O|NhDyWJ79~RtI4*qBC0$TD&U?i9zj%q6&z$aY7c5gKIvA0-GdOmAg-}5$rJL>DU&KjEwG)NHsHyFWiQFlRoS)6_Ai8?qGKK8PE-8IQL6h78(M!K0?WI@(0dNz}>;V#_;nsb{mn}f(;*Z#dEsO%4$(bB;xPTDaP1)1+UMjnA{7j_u6NtTxDocx1$;9uo3-zTx++aK@7W2S#Qj^D%LZGp=ooTM4eAbKWCXTAJPn$c$6=G=e2mmtkp<e#qvPTkMG*et&8L=1y+<=<AsHL|oQDHQxqs#T_cSGm`d>Z(NemY#cmQ39O=z97d+Y&59L7KV6bZys&J8ElVW_UMI&F1-SKM8kLFSSgJ?FdP;;q(SRf9v~4w2z!u=jj6y2*7RP)EtGGu_ZdZ^xH~rNMvJk4Bmq)mmv_YI!AOow5avXe7Yp$13c#}tdohdSy!8*o{YxiT~WP5eXJzYW86zHAN2N7y#aD$VqDgI33sdm7E5?U)FcZ3P`VZL4Dhy}6Nf?*4}r{(Z^|aPp)?k;I^9t{q*RvzPkZ^6tbnKL9<wpJ9e`9B@T#G@;=Qv@t9CZcZpT1b_H`)BHqYjSPYx{I2*65aglXI;FXwCvm~l}{ASZY3I<xKIT(%lS4)F^N0mv(-*{wIO75LE*ntVZOD)UudBg}#~)rI?bP0bh7mSk-vJJKB(bHVl%RA+Ssdv)gPFF*`~J708pQk#hY6<K5mv#jQ_G3cEDfa6+YFfh@1_H1kQJ&9IL*2yWVDil{mRSM1iGk;QcnwobJ+Sii^$OoSH)_6C;pj;-#mJsYj=OSsxl&lHnE#oE(G4>iTtg#Xq1x~<GDNd|$J3JlmVlgnJ($mS#H3C6?K&ti^ExHPoSrp!t5gaH{kW1v^x(2n7rB2w#C4Mf>FFmNY_Qa>G7MeP<#R_ht(8+m7r+vQ=SMb82(!ul}^@Dl2DrTeQT}k<4q*@c4dDE-mA_LLtHWSf^cA&7jUIYa+5;{P<8x<-SG;PoKv`ePZOTTV3xj<K)I_&FSO-OvaqY9l>$^JN1q9i0;;$aK}hOv~Td%yOiB+@L^ls$v$C~xGOb#)z6GJ|18j!xm^cyJu);mFwKo&om~y`N)~Qk1FE#_G4Z1Han`&=S-F%@$%Y#2XlPrzD<$T)Y;i&xqn1Pqy-AH%a8y3nC+8awzj8pd$}AvL*{R?N~ZG7@gjGAy;?MBdBI(OkB((BlxJc5H<1@B$XKu(GhQMgUfMyvlh$1baY!7{-ak>s6Bq>?8|z<w!OSD*01cOk4UCKp=@z-nDWOON%^vE#DH|@ZF(5XX@X8bvsB>KLzz^x$el{Qw56&T^$5%~wDLri-A8>@#;8JN_lmK}Vkl3KZX!}B-zlhP(@`y`sL{fVEEGGpbss51=~_|Y4bQB&n*V{h1UL*4<}Q7-b|E5-oD@FLHt7x~r@8qVzWR4+HuUuHO%xSkgpjS$;exTh2Rm4YIyST_vQFE@MZ}CHFZn(<AiszCr7Qz@^@CJ$m1%N)Eumz2_dcM|Ue0H@E~;EyZ_Uh}Scq_kBM6k~V{&}=(_8!2%Jx1C+{?}6n7D32lG^m8W^}5@jApOx{}d3xW^hLoMaYfBT19*($$CRop*WFx0{JnEwMBL+t~Ct5F@_;j@<Bzh&;)qS?6E77&re_JYxcV?3rK&pgo$S`Y~g+Gm_ITAuz))E2uW}WdcYL$sf@r-YKa%tAiyid9UW_MMfYoF3a|pKQY_H17HesJS`?Z9@(2qr$eBpzFwbnLBdtnAO4t&bMCKmUo+fPrfDV-6Sbx<MkmhinLJx!s1rlGU9@5mL($PH9DiWHVVu9%6mP>%*=ajoMx&pa0SV99(A@dOH7^hsY*)6%7*d;Yv|9WXM#FR97p#(u!;x;dF1)Npo{rJ`Uf(~8m#ZcXx@O&Ilk>Rj$69FcRH!s`p{A~`v@yXd9Pfg3k)SKGXdlz;<_Z2&!-^C4xbhXoR!hOM<+0?qrRrDjpYw;Ymp?<TySvM3*v8Z^fkbuolg>eY$01NExnB#LI+$Aa+Qj6&bg_I`_Yp%d-;BUXYefQmOZyrwvmFF@Y@s5QHE4!ZA8W^rF1L=@%feE|5H-<?DVO*9QC<J*ecfj!s#U25y1i)i0{;dj`aM{@O6e<K%2%O8s49#wB$-$G5TfoSUPzcVBXOK=%mMDcxv*YCo5vKNL53SjOqS2Udo_}eER#x&zi_5>!O~498@o1zX@t=wlg7sCU2k}Y)Dqi}sLpk1RrK|(#$}P2nY!%}bH^_{~sU@3HpjJw8`IcC}4+g0)9N=!ZS&B<|4qP?mndTgWqEZSHNu0_4Q@?x=Q?qg92IMgHM?UQ%=TcqpDr#yke$~B?I=A`R_B6DUo$n51%ivU`ZtP<h4VZP@K`%bCulRuTPqG3SW;(4~L`r^yBCMgR)`V4o)MDd{*&iljP+n)GuJZLpU%k4o%7&e<C2CHP7ncviuUfg<)J?)o#*!sI$;I41dr|0Ukt+{{V9}9qxkSV}T8urJOToJtKzJ&9F4J-k)t9nVwim^&!jodbfg3~|GtNS-xX=4V3{xOL(ev%NnvY5xWEt%M4orDzqELdv?ITG$Y@CK})X;vvsX3|o(!817?IMXs3(oI&wx=KJPc;2xt?9Jk8bw^OQ%4ha49LSO@TZG&x+a0k9OM<(AKp@0ZW>U?7*lt#0FCF9b6<<@#hfFCMzTeu?Sx;3L;fLjZFU8tI#%aq%jhy8fwSJRj)Vp6s#6Rvy+2MD;G@}a>H+RCM!+*1+t=SUB}bBYY@dc#bZF9gtY9_JzFKS@Fs|@okk+ScA0K~w{qd1D!e2eiLfpf<$Dc^9Aezso*(8#XQif~|uh7T?kKr4R@N(e(6AUp^*#B#M<M;|3b==qGF}!TeoG*wJ5dK_44zdAKcY!o5bAYoKf0mJ+_amSF7;*gBc?P~BElL0N1PbO{Y(JPcl9q!$e|O!OC!>oW#pIU@qD!Ct`S~k+g{FD+?R+5s%yqkq#k%W1sdJRh!2Fx*{`OzK=Jii+e|-IQxF3%bw~Nc$AAUF-e)gDF7r@t-uS&Xz03P=B(+t>j{@~N4By~6XTTh6q&mZ~ti$YNmL9E5M$QwK#2IBrOUHJN^q8%%NVXTD8zIZwADfs`idxa^o94~$aXVC7`w<YgT_3?N~x7o1+rV{uyhIf%=6rc?S+S4%rCUe!gMI!M;#yW&B-G`oQ4$^^*9}+HV<O$Ed$Q*xLShC<lf*O&^e5d}qIXspOGw065Vcr#nnLY1ZEcW#2A+CAxIj^8!rCvEX-ge-?8&Fs>-g=?c0L5TnQ_Fy78Bp>-6`?ZqGfxK;&`$J|9X6nh$gw7rC!zOX8IA(|AjD5KOS6K|M(M=16fb?Div=HejWLOk1MmZ0U-kjOp(<LGw`t;H6vuN<8Ye@`qQGo)`JJxt=^+a>CKu^GYTRJ{J7FYy`-*UeUwxUm#7^&e7cIWQSIe}c{BJ3WJFdE7#sF@dE~}o+;FC_`QT~*dQa$azbUX`2bc2MoSUts%6%I!)OSBCW=51B#iT$2D^id&*eV?2cWPsBaTyuC^EO~o0J1~}`BOF}0T5Gx%yyuFexi(~^7u&(fF^+}pY<*kU6p($7oqSot4d6}X8?c`P(>c(KF~-O%r#E6d?5$v`B!;%fjR)JIc-~{+TU%qA&^_1^StxvAj_EO;6B&Sv%`vKk@GKRHLTIuZpa|N+nfJmH;u1l@>_&i6ss2}gtGKU?`W^1BP{C#TkHIkgDjhAJTu;B~-w~LmwP>xxziV@}7{#Gntt9~2mgHfxfyd1SjL0{SModQX^Tj3T-mEE82pRbV)rX+>-LPud3WRq4PjSsW5E1RNh-iIa>52STtD_0B*fm2e%0!c&^CJirg++Vm0K1UiZ$BHrJ58EgE028;wHZIu3F9)XN;#~%>xXrPPR^*(($Nt5Y0UpMQC2IsVkQ$>Shr+eGNw$zRCQNZNvN-1qvphv-a92HkN-D3IDo>QX?XCA@oWr4e4mL5^^=GwbUHC4_sEqjM<ipQ7C>eRxRK4+`9sw;<WzEYP@pxcgv+>QX7>rF1QxH%<MdwH_qi8dFTxk@f>bHf=&^GX<aaUxM==Aq>sPaQ9duory!-RFHH8i{?gEbiTG>z^(~H5c2p6{)WRq%GmBJXJSPXB;_ZaOI2Uj)ej*0K)kg8vXZE6azbJhB_!Ch3?TuhcGTOUZj$?u~gB2q06t@6n+J*65satH-=zV`k?v@DX^sGL6xCl<?{lR@!<`FO>bvm`GVukN8PScTRzu0$i=rTaf+HCBaKeY={H!*QoiyBDCi4vU4SoJ~c4i;Efxoi;X%M;c(d<bKv6^;+F)L85zB?J(DRE>n%Sn|@2gRZT5jqofyCo*DEhCYD@cK!F_yj>k}-sL1P@!5IOUHL2s;B*xi5bo&}h)dbY<jWB#h(7l(c-^!(e%2|H>4Jw!d^PUU$^z)|jo#Llr5j-O=RLb`<6pErdIg`~Lf#N-cMg^0^$=)&2Y$tS#xOH|hmjDWIX+hGxZJr^4uD&cX<wz!zMs#b@h-QtE9CtT;D-H}LggT*jyfkWoL3hEF)SPlVHhyLjFBBXC$Tv{LBSfsWNY_Zkm=%a5W0h($47?}00M!<U9`#~ZGgE<0*Aa3m;z1%v8^Gf8o#JkqGH(pcNoF$dPbMyDn!DjyPif~OE5$rZo)kmfkQF+KBx?zqX9c5_<3#Q|FAlyc><gwzLT9;c-3OTxTIHjo-NpK&OLp1dUG-_LJH7JEbFI)SCFj)%W`W4RxQv&EUA)*VE=6_^dt_CqLs%L!EEZ<z#=n1@p?)J7rJhMBa_JGCM0Sd&>v=e`y>=;3v4;MI?&ifuB1_iYEGtHwc{0p$sf`!udGPOK1Y?@B3|ohk%Rvat1YpbJ>n;wFja77kI&B5lj4TD&xf=1#X`%e?L(J}QHy6j&4M}ZoOJbQ6A(f9@N2s2ggHT~8ecIRZ1ZRxs+S_C{Mmc%BYu?K(sgJqR<~;W=(jKUWDzon^v<Gk7Q6;(pW^YHc^j`1DGUJp@mlh!stG2nhEcFT+Sb}1mIP{(c>8n^bg4GFzo9QQXYh0|zhAgP)kzL52fp8#6v<Nyomtip<OgW7LV8PP9*@6%~myeGpJ~@LW(QcTnm0xUT&vI9GaDjikted=`+k{W>!Z5ToW}{oW3Sd+KV&A#^@4aU-nLopmu<kZ(Pu-(z`J#?mYw5&JVQc~-Yt^L^YMPQ<|Jba3?`mi}6<4bgbnKm7Z;5$cyG3(!I>+TBJ+0G%UCFSt66VI=0jnW1F6oR^tSrRr5*+7&{&RhPtR}t&Rs`DAU`S#P&J*Es*Q$<v_rZ1XF2Hsmgi-0Wl4=&--94$`{z5fL7&3<E-qdT0ZP-YNdSvG|&z)h4t6|#W&f$$_P&b%4#f;l2%~)}pi*q|-An@bEkiW}6BmbbDGHtG7x_Ej-IyigII^LtmM7Dm6e_Sne1W08>{i)#s=OR6E=PNzq3eI`t3ZyPH46dy4pi!O$Cq=Ii3Zse<-+$9~TStyg<1{yl;({JlkhAg7o=Ngi#goPLXk6o#0a%wEM^C(StxBv-O#xA2Oq}Bbi*Z&_C;^gYRpz9WeMe+RBnphFh05S!5zmIN7I~Zmd3oKLaqxPHmKK}nn2ae=OrgC(A7?7(Az9EMd7MLm_tLD5nV_HC6E%{7=^?pAr(zUOJE#ETu8^XZGE~+g%rnfmn|DStHZ%(z_O9~;8(>|m;N7f7l3r*ldO=?09#&68weOb|lU9_<XuyZ`3S#gsH!UzK$^;hBHw#GH`YiFFjS5x+2B&pEy3?I@eJJEqmO~3@S4c&2``AR~Ps42UHk{dlWaS;od-37VD&f3L9_a143~TCXA0!B6ElNIbEmIahC%jvY1+A1cejh^N8Yn1v!PXBy?1eMn_m7Vs4zkI$E8Im<Ta{*}cMW-WxUT|3#cy**VC(UVdJO&MUI3{zrJ$;(abF>cgvqLmJHU?*NnRw}&pwG%^#iic;{6;bN~r5249BEvaUf99WdLVntR0yK3Rg9m6RaHShzu033iC)}NkW(>oowCi5q=!w5+;9u7uKHd%Xg{u^5vToVph0dIzZ?T=$8OhZ<Aqs_Qu=$TQ@OTon9PRiu?|}{ha4?>>h8o6=(y>UC~ujz%gT{FUO}hW$&!Bzym`)1t;>RY(#j(7oG1$-s=oW<aD}qGa=dEo+yiN9+zq~GE|RHqSN>pC-|M2fN~Xz#ijFknq!9n22Lij+&ws%yn@@xo~nRW<a|0*aEKFBQ`Vack1&dlnq}uaiF9MB=ZA9`;O!P}@z;Ivawm&<NYSF8exh!S-OtmdzG?&S;|w_8=XEn=on=Uy1Y|bqE%`KZ12F0!)rd{Ggz6c^U_;d{8zb&@uo>o98wq*Vqfz|9#fvd=71H&V3U7sf13gXURo}G8bzan%h_XHuHhvMsC2BakRfQr(8bSdq8;gE@i|h8Bsz(x~P|*pY*ksV73GXn`^HJ(t9cZbHB4hJ;x*>vdT8n<|auACoH06L0a`N325GfSv8&k>a0Vuc91@mUKmW{1NN)(%94|j4_hhwIq5n?o*uhN%sLyjV_(=3WlAxouq!tq#-*ER+GIPo<RsACZIf;f>o$(W^;Ul^sp9oc#=z>qd;;Qt`cLm5AycH6s{J{E^@0ziFTLENc5w9ssk+PB@)$_O=mhk4FTjimxq`vJotu?Q@Q=T2X7=aYc$<(}O~x@@ZwPFT;4FAhdbQ@gxePkjL~6Q(TJ3~6}v*%}OJkNXG~_QBi$#?t=9lmbfX-F=Mt6XqGeN!NDf6q*B?D84aS)ioV_-NMWr=Qc{_Lo<^4T=%1N2g2KR>d@G+u3QU~vcPs~q6l=J(3mrcaWRdc;>!6w82j=%$pbbYsFOlvH_#eZD?|~DMY(n-_+z1tAmoGLKr~PXeNgcKP<drvYdSHhZ>oh`@#F$4Him~7_W{lnb9f}ELE(x)lgj@jJ4li~&4qSQNe4X60u>)(GM|{nKzaIrBp)VQ{3jpA3g<J(HYiOiLS&9(3@z+QC1Y3O?5$@z93(lJ*k*t|KimMDNI1`>O6VR%8)8P!xN|C6dzW$k@etYyh=RbI6U-gj+n#MG$@iIYQK-6LkcYF_8If)3Hl_d<7&jMiWi110Fevt9%n+0X2G_I9H&Cze^u3hy_=sz_{V`SkNf|T4SZ08{XYlB$@I*`R4;;twH{vzs_UyGaVNW^MB{I{Lh9tTqi}))dZ|XNx_d)APTBNh<9)@P<ARYRtB+9B@K38f9&?d1jov#aAF@k;UlA|btPcT{y>NaFowJ!_eDe4>*VW8t`WWTi-k)nqM4<TzBH=|U>TtN6ev3W|Q5|Qu&piM9qwnSc$_YRhY-j!9JMh{PKHVu$~ju_3D%Uy5^aefWFC<_F^ng_HMPcaZBKoG#<*&VTt{s;#z0VSw91Tsx%)@hNPp-E%>?)fsI&4SEPxjb#Xt~Qlww&!hkX?fbw=E%9If~NEzN4is9rB62m_T8k{V|OkVTha=dKh^E1Q6K4URH{(0h7+;~Xcf|!>PIvA7LV{yeA2qq$1r1z8p>M}d}KuO$R>UL6(~bdqFr)URn~z+%BS5PU(~(loLq#*6grkH-28^k%Q&mSHk?vVx1vb`KMzU9FtL6`yl^=zerxqP;ap_*Pc=@6s7Mln&iflXd44KM`6B~J#kTUg5cCRcMh8?Z4Y4wf#xU<H#ua&33#MquL$q$33St>-BudnPM2!%Cl!vuxm~<8PvpAop-f?_{1$Gd*i(Omff{{)@jRRKXbqU8+wvH_wWT=;=<K?J`o&OG4sDN8v+|bz7p@8(>f-0fVJAo$ak#SuUnv&O=C+OkGaD?>1L6uW(fS!^k05f=9ZcmABt5*X*LocJ{tp(Gpa?Q%HO_R;^M#;jLln6M1nCf}3y1$%kMS;Qe`Lel(K3epgGf}QK@W*#ySnVawD@Saqc?iTTePw&CDwka5mKK#VwzKQg&pZ^<T@!nF`V|p5*~SBJ>wi?pWB00adiehPQ#kpJz_@`P3cA%)GKUdfL3a9*lD%=hx)0{wJz2n9c5cpA4nlrjAJS5SIZHS<wTd`2lW7Y(1Z`z()Ny$_q(o$|87{Aacsj+*HcDO4qFUI=Rs=A%Yj9M!P%cVT=-OAPlRIKf?E?1YVUEd*Ugto}#ci^xT|q68u@y5}lQF?0f@S0iRrBzy;tElS0+>lVipt_o_~`9}d-%txJRb{S=D3cJ;ODOz7Ij;xcbe9>`BVT&hA8rQfis!AghYlMyyCNB<(kQzQZ=l0k_i$u%BSINWzxPnNsKw#lB9qpw{AOWW)h58XhoDGeeaoLUMcKQOyW7<YoL7h_It3RETx}Dz(SWd%jc!6T8}Vj%goG&$8`Z0n~^a19Nq<=-vogCv1if6sBnZ;xxxUcfMNq`)zIlytlIdpuR<zkJVu<V5IhWrTa^vYxl4fEmIpg)UNzVbs~V($YpRg80y*p(r=uL56)Q5$uvsW})2K<*K&I@BWBD)~gKHMz)CWivA`+fi>cn?)qsk(PUJVo*msRD^0K4H=xWEFs2bBN8$x|@YA&PxfT0k5cM5_r&F}UiG(^U2Jg;9b}0Ja?x6^z6-a74UZY#DqYjDk|dg)zw+*)-L^I+|q^NaR(|kYZih25qd<2F6}s7ew_!V<y2Bs>Y5Wy~Ksf=9yuo+by^qCEXoIuU6OD5k6=}x4b=x=d`^Af$67nMc0m2Y$&wK9ceBXiStQVy%*Jiq_aW9Lo~5BBQs2A3HzJ5#K(P6<fKwlaltMQ!j~f2JaM~tH$_b>Cagrip>$7AS3mW+n9sNhwUVXyXg=TTd=62<$lf{q_8WWegzfeGf{EX$u!hKecm>FGCh@nOq(&=P_MFQ^tK5Ec*DcPV#sb=BUFgNRn#eY0Nz!{&5K1FkEHIa<Kr_;c-(dx0V;B@;7+;}M|2{e;nu$HfA3<-86&)g>Aq0h*%#Z-+zgDX56XwE0z<DG{7{|heofVF-+*U?QwE1Ib2Ifj!R=LO^@82b9dFSF-%L8tD>~pD)@gQ9;MmBYX$9wtRGOl@9su6-SuhXOUyKKGUP)s%*N@mt$(SD^Pi1jcXW<*TugwH{<Bhn1YGl<&)EVCG;LcgtYn}oExnrbF;fSv>(vvh3(5FJ%rH5t@2<(V+LqM$+Vq#4$f!W$#o?r1%nsj@N0=k7#T@?ROe#U!~18nH8$)G^lWL6mfUlU3Q%K42#Fv`j^(3E4_VTyz>C;FB^-OJZ}v68mnOO|bNw@?&Eoq5|p^Z4xfkO<Coo{zFCjj#Q}9;s;fyj}fwRT=vhtd$Zy}3I`GYoYsT60B~BFGkQ|X^Bk58s?2`^OS1$V7UiY(+KVF`U9gC0o78kw+IY-Rgabn2KT4#``A@DTdjLS5lS&F`j^DL}5f>52(u1HcbPqQ<559RF>3_`7A=?p<63a}UbuhC|nKVo<Nei;)MdJ&C?!<+J@Tz-NOp=Cb{1SS$z9a$mhX6@mhYF0VU^_flZ<^*arUIOUwBX<s-a$+YQAJUy2CRY#ZTVRZ>wEG5u4r1uAs>Y&OYJerrrjwWXrnwBB!in7XNfEiB3y`2S`*q#Tj#83RS5Er<Mq^d34*y{$vur@w3;{;x>V%=CLDWK!Do^-Nl}^VoE>zw-qYnsb$7?AKHw{3v!8XgF2Qno+P91Zjn!#TZbYTmrFt~iBRfrmy%3OukHv>#a(bT>;M_v0=B$GH=%K2^xB|8!D_1B6gownng(-_j%}r4_)j{-4MqZ6j;n;FOL>&WvQ`jbJ@}fC<1`?eMrH@Sj(`}SWp4vdCSpn~)uuaP+&c$7UK?ai@)fPBIuMFJXDyd2&?z{jkh!o&=t*%Jd1Oxd1YX-b;pvzNF<&kNrB!eV__jg6EQYaM~;vbe`6O;z@Q<_2pGB1TO**_$?hn}V*Z(8Es#_-ox1fY(_YgDjRgljhWSOy~zy>(jR!Qj<1?uu8~Xy#C)1H#zTq&+88P&_@n5=ulScHp?HHF}#Gd0<uPA1egKq+Se|Tn>MWarUy%q!o7&%A2Q;C{|sDLa;1_<r;Kp&Kcx}0?T-Q#E>%h5{VY@8pyk3=Cl2-;v!kM7@_)r2g47DEUdK}!3ijtm7Pi5p#ZAR3hna}isQmKTTcfeEg>Ym)8|ryB1~6xNK3ahX%*%sMNy<72b`-M)VfQoDbDaHs8m+rz?9xEJQxf_Lh532cFWRQACAR#4ko#1@T!oG!Ww0XyeI|Kxp@j6?Xuh{^H3nUNElc|edL)bnDS&%ItsEB-(e1<Qj#w_X?RtL+h?yrP}@J4+1_(T3iEB``XH|9q2RNWHBGYzB}JD~QSyx%#3ZLpQ~bKk<ndrYRxFk`6%wMI<VIgoVUS^4S7J^9r0yUkRbgzL2yTfE4ab?Xw4d`4Ly2rj=hd5ICPtmhH}2BluamAfs|L)&oR7QkElpZ%z1*ON<&pAd6#jl(htjfI?$z=DOt%@7K+f`e-AxjBYmy2cxjc#uhiaEF?DDJ6yq4*0&&7gvQcFEmGCyFKb&P)sBg8Xy06mk4<3NGf|4<>&W)tXg;4#^^3M;KAz0lGj$gna}IKm(ll6F9eJjbAnIQM0UO;3ff6iA_oDxdtc$gB-`l2VX4Iqr2o6nKw$pdA5>pkm8~GReL#zX28b>df3!9*Bt0b%|CvB~tB%WMO(w#SpIGy(y#3#){gx6fMc!?=&oyZu>sprVc2<Cu<x-51yyij9<)G&~{q4DU{6pDvku1JSf1!ohtRrs3-d{Zrg81@8PB<T;0OJZS*xt+BUIq@1qA9-F173RZLI>b3K;{5y<S)RVj}Y!ul0^t*Hf7s}xl<N1B2FUM5Z3+jZ5EF6SN&IJ0$FrPA;I8qJPS5ZCYLkY$CssR8rUvaEMay_YlLZjcZ<R};0O1BNoNkO~?;>wqFU6%G!cVB!i|)2L%r1nP3h)<ZVa<EZKH0ZAzLrG=atXky{RAaH#;cn_fC{2~FUHX+~8pbDGDHD<p3gZO~-rk%ZM4x}h(P&4c&pH?I_?3_;$RGvuN7q|Rl(VWRxtZ~Zsl#E%Oh6vn}hWdEV4xjPH%~nzk&!HMUf(LW29gcHUFu(h+_oYu)R{_QKwILQyVpUCGCZ|WTR(_~zEI}^CC)HXyM5>bWl&Zh{w1QO$^k7wxL{0!+0@Vp3V5d;SNR9bQc7#lrg%n}7s})oh@#=GfY^s(t7W`u;xeulX&BW<12OkwdG+YtFcKvk;FoJ7SC^XO`freuQ)=R#@_Al8Lt|^s$GO0ACQxp1!+A-7vkh2m*iSSGUGXT3S0}JT5t~e=VeAv;Y#Y2b?m_@uZ9JaZ@=srI+2uQcXv(JbWu#3(#NAi{=hu!C!A|;QhnVy&6<XV39sgP*JNzSxMnG)cz!bfRk_*y=^fo_I~Wp)!!5qgD6Rc>(TV@$Dvpaulk4tmvPE$u?Rb?XX3Fx&(a14%CuHOVuef{si};C4^G$5M~)L`krcAx|CY;-&TD<uLC0Fbx4IIT$X)y{5CF?oA_A3e}cleNLjYy~nUEU}G6WX3+B_y9yJGZwh-!B{IY>&W#s6LmHBeJ<OFC5<LsT$*~36J%H%OYzebXTHg<yH5y`E(@5?Jk(6RPokiUZC^$^95)X9~8l|x63X|@W9Gp+~uUCD;@32^TI2w)z?Cj%U5T}q%FOLE1xPTNnY-R;D@~0h7=88l-w<J*^fFbrc2q8imLm*NDFjNY)Y07gP-Ep$z{-iIoNiDiv)AnRyA$Yt6Eb3Sj9C38aZK8oO;^KaNx3iK55Q^C1EI)s$fQoW4(l!?Q@S$Omr=EqMHd~Xwm@~HGY04T&x1*s<7X}njLr(=++mjru&Fi2<<OV6Z3sDy_v#G=N*3!~QXD073?~~+_LFdg5=2E(5)6a}Z<2B}VriZBA#@|-_H_Of6SkH7V;tO=0IAL;%LERdI(v3Wj6L|klYhcEphMz|j6d;voC(@RgS18#RjfAnlBF=ZpWp-?CH&hy)wkR2Lz;WS|F6n~Oao!`&|HVtpeCBkIyI`3@(ZPtsox!o|D})M4Dcx-E{vu9Vs+}klMon#3Oyo{k<os-Y2hr8@mMLUUc1h_g3Yz2&h+g^~X)nbR2!NY#W)F}c4Y%$qzH9+P7k|VyY+)4WOwQz(!v%!UZpxmn_fpw~<7XnJpFr$oR9RZAN+y1vU8pbp;RfSLv6u&@lbSr96atN{?M!nW<+EN~H*r**ecIe1t`I|$M*xtS5B2i@mOYaAqM73I%811v;0Dy>MJ>H$i3+1h9bK+ZzZ*gq;M2fA^wZ(mwPflRK-bgv*p^@+3ewCirfa)K+)-N_GsC-yYBtYr`$@Q~dZ}e%Y)43%4W~Eo`CH#VqJ8ANI!_;vKmcwNr{*Zkj4jdOrQcS1Ln0fSWAGkaxeS4D)j6W$p+&84=F=r1AK*D>VVz8r&AQqg^<*?A?~3Xj>SHCD9^+nu`JlIt>J5-16XUYxOSoeluvo$)q9#%JhtjQ}XMnf;oH!JkcnD;Md{Z{T4W+S&)#;AvA*H$$c-qUiWCc7`_n3{*?Es|8fL9IG74MyOTD7xjb~^^jvadr~ws|%ud~#svMgUeaBTVB)c{yiWz>JGp0y(*J*O_ex=d#rxa)@7G2tZyr&2GJMt-z0l(BunJQ<<;w8etZ^sV>~dYihorwj^sa*^%zRm<zVApgOB7*sC*Ne*t0`-1(x*liExKsK_Eim}NDWjY01O036pEgMo?8vu9hY?@6?3vQAD>RiU^ls#0k7pZSxr)6~3+(7v8TKtAxix5m2(2IVp_wuE3OIu}VhresYpZy7gXh_TmzVU3l@C~yLfN^xS1+u`Ye7mI-*m7Y#^t`P|G15&lWXwg-u%%bqFjNm|tf?OgO*EOhxEOo*@F7b15e(6EIwI@Dhwb0a=Emm+Fg-*^xI_>*~xPliBl@6x=s2|MBRWTba?@G!aBh{MV%$r^f7a53Fx0#4Wv;&3J^&%*sk<bC+-KbExplN%)r(H6QUix*T$pyOV)L~!uYC_`U9aZS8O7_R85+xz&5)We-FpQ-v-TSpCC6Q*SrtBG1M|mUPtgGvok{Jv$a&!tO$AjZY4@br>_YAm~==~g<l%h<PHdepQ9r)cofR>;ZXtofGA>P2SJ0<Z1<l?nBeMS`Dc(Ro@yGbIqUJw}(lS7#&0Udd`ku_PkX~)vh!RYkf3%R<39ziuTW8z{S8No-jg{YCQAgRoNh>m!38(fato3&U5rlZ@!@E^U3LhbQ0XJ6I>w(aGOv3_MIeMB+^3T2Cv!<0YPNXnOOBL<{HZ_~qAP7`zjnxz7-9?GPmMebDcr7cy(s7GL?p_M19>^|zNGDa0DyH|`&7DIV@bQ6(6`A$JSn~rKhMU56_WTDu(t@}tBO4o`CZ+K?K)%*|4CBR{bFn8&rwF?nx<fQO{wn=v|InB+_@YTOlv!SPlZ=$FWBZO>~4i}95J=noI)Ulyek#*WGE+S?udCB*=0r@@5FJ&3Ps~@D2t4x#YYY8RGyY~Tw_HsVMby4NwdTVC(#6pBS96_K=ACu#|pWfQHR<`$H;9hPf$Ha9LlGLUzHKS8KW;A<k|EGWmHiJ8&C_-)|)+*vVN!A;x3dM=k6UdKQtSz!rajjwajWG<Nk`F41g(kprW{+Kwe17^$U$ftJSwQ-$B}_bnVGHkb$NZ52fCbdKM@WK8&;zD`Ph|v#QcJwB1_53v?&w&9E4p7ZQ-Bp<m12R8wOC8*)1uG>kVjZ}LC!=vhk0g09cfh}Qo@$dBr^A)_B3f50Cb=f$NH<DfHa5m6nY?BD3JI%^^m3}m5%0-R*}%`6bnQjw_E}gKd0QC(G|$0!4evP3Ymvk$2jGJ&2Guv#4f4X`qxX7A*Q6s3nd7;61RDYE8wgu@5is+7j)=iFNW&ogy-XciVTO1n+Pyjym{G%=WlZWj!(|^cxqZMrry-9-n*~^y06#){Vr}mq^q5l6YdM<%%;{|uA(0)UW@0j4fUJt&AOpjibcg+g#>JdDvU!|2UuWl#~hy%;Vx0pkXlSfD5N}bSaStt1AqJF?Yr-Od-HfYs63bHh<7YpSlRW=*1&Le8Ayk83ryJcy)jHO2;;KcKq1I$xdV=8DE0_oB>*04@o!bggv-XJr%)lFLf~93W@vV6OAeld+yX{+ghFt3JcD$CvP3ClnjJ4!h%mJ`duYuL6phAw^ZZLQw6c;%T3r5(ZUR;)ibo?AiT_lb5Uj5%J&0EdQ1Q~29m?@mD`g!>S8k~tWUCmjxItz-PA%Dt0<}_#%eTb(eK1Ic;Q)8L%~D*#bKt5e&ot*46qQntNa9TPpZev4n3|0%Hz0?pKk{iGIhX2!S5Z@Y@vH8A)Va;iwx^+;?0k19TLz~hbz>j9Xuz!F4tnvCeZ>cyf07lzFw<$>B2w}r6k!cjwI-|zq!t@r%>FPLgYr5fb(OC-`s&qvRW|H=Em3oVytsTAe$~p=rfw2$GL|gyNiOF8*^5F)i(Gjq1dEP@%OxV-(PHe$TngUJ0K!w*bD5TVsJ@h?vb`vF6`m9e4%{H(m~j?r#eLo{VweH}ik@%B)qGUqAj@b6aA3+y6NM5SZXZe7VdFG(qlWhTP0dNwm*&mvZWl>BT5x{HvpxM#f1>FpYfYyO*C^tOojRJZV?Z8Ofj?cG(=`cP<{+=Q{_vL4a?^l9#+bT`1!z2<ocmgIFXkLEG?FbMZ72LP9P$sLYqKjD)v-D^TSk`&37qwgbtEikSDj*b>HTrK03XeUQx9;DF#?|9*uMU*DLInFWBW9`qC=C`V+E^$_SItRfN_NvgS0+n`}p|d>yMAL5&r677UCY>J^n;;1<`yy%_fnAlrm&%c!fqDcnsfggqH*NpJ0fY!v0_58^>4RsN=pakKtu&=6pe<fbi!Ua*z#>x(lRfnFE}?__K`kydU}W$B5(4&NJ{8X-WF8Cr~iwV*A0ok+dB2`Mc}JJQ-d5C?>yL5MBE8&rhHJKXz%n-T'
ACTIONS = json.loads(zlib.decompress(base64.b85decode(_BLOB)))

def agent(observation, configuration):
    p = int(observation.get("player", 0))
    step = min(int(observation.get("step", 0)), len(ACTIONS[p]) - 1)
    action = copy.deepcopy(ACTIONS[p][step])
    action["hands"] = action.get("hands", [])[:len(observation["farms"][p]["hands"])]
    return action

act = agent

```

## Rust market overlay implementation

### Source: `kaggriculture_meta_lab/rust_port/src/overlay.rs`

```rs
//! Small state-dependent market policy layered over an immutable unit tape.
use crate::{
    data::{Item, ACCESS, BOARD_SIZE, ITEM_COUNT},
    engine::{Game, Tile},
    tape::{Action, OrderKind, UnitAction},
};
use serde::Deserialize;

#[derive(Clone, Debug, Deserialize)]
#[serde(default, deny_unknown_fields)]
pub struct MarketOverlay {
    pub enabled: bool,
    pub start_day: i64,
    pub buy_stop_day: i64,
    pub endgame_day: i64,
    pub cash_reserve: f64,
    pub sell_fraction_bp: u32,
    pub endgame_sell_fraction_bp: u32,
    pub wheat_reserve: i64,
    pub carrot_reserve: i64,
    pub tomato_reserve: i64,
    pub strawberry_reserve: i64,
    pub melon_reserve: i64,
    pub egg_reserve: i64,
    pub milk_reserve: i64,
    pub wool_reserve: i64,
    pub fertilizer_reserve: i64,
    pub min_wheat_price: f64,
    pub min_carrot_price: f64,
    pub min_tomato_price: f64,
    pub min_strawberry_price: f64,
    pub min_melon_price: f64,
    pub min_egg_price: f64,
    pub min_milk_price: f64,
    pub min_wool_price: f64,
    pub min_fertilizer_price: f64,
}

impl Default for MarketOverlay {
    fn default() -> Self {
        Self {
            enabled: false,
            start_day: 0,
            buy_stop_day: 30,
            endgame_day: 27,
            cash_reserve: 0.0,
            sell_fraction_bp: 10_000,
            endgame_sell_fraction_bp: 10_000,
            wheat_reserve: 0,
            carrot_reserve: 0,
            tomato_reserve: 0,
            strawberry_reserve: 0,
            melon_reserve: 0,
            egg_reserve: 0,
            milk_reserve: 0,
            wool_reserve: 0,
            fertilizer_reserve: 0,
            min_wheat_price: 0.0,
            min_carrot_price: 0.0,
            min_tomato_price: 0.0,
            min_strawberry_price: 0.0,
            min_melon_price: 0.0,
            min_egg_price: 0.0,
            min_milk_price: 0.0,
            min_wool_price: 0.0,
            min_fertilizer_price: 0.0,
        }
    }
}

impl MarketOverlay {
    pub fn from_json(value: &serde_json::Value) -> Result<Self, String> {
        let profile: Self = serde_json::from_value(value.clone()).map_err(|e| e.to_string())?;
        profile.validate()?;
        Ok(profile)
    }

    pub fn validate(&self) -> Result<(), String> {
        if self.start_day < 0 || self.buy_stop_day < 0 || self.endgame_day < 0 {
            return Err("overlay days must be non-negative".into());
        }
        if self.sell_fraction_bp > 10_000 || self.endgame_sell_fraction_bp > 10_000 {
            return Err("overlay sell fractions must be in 0..=10000 basis points".into());
        }
        let prices = [
            self.cash_reserve,
            self.min_wheat_price,
            self.min_carrot_price,
            self.min_tomato_price,
            self.min_strawberry_price,
            self.min_melon_price,
            self.min_egg_price,
            self.min_milk_price,
            self.min_wool_price,
            self.min_fertilizer_price,
        ];
        if prices.iter().any(|v| !v.is_finite() || *v < 0.0) {
            return Err(
                "overlay money and price thresholds must be finite and non-negative".into(),
            );
        }
        if [
            self.wheat_reserve,
            self.carrot_reserve,
            self.tomato_reserve,
            self.strawberry_reserve,
            self.melon_reserve,
            self.egg_reserve,
            self.milk_reserve,
            self.wool_reserve,
            self.fertilizer_reserve,
        ]
        .iter()
        .any(|v| *v < 0)
        {
            return Err("overlay inventory reserves must be non-negative".into());
        }
        Ok(())
    }

    fn reserve(&self, item: Item) -> i64 {
        match item {
            Item::Wheat => self.wheat_reserve,
            Item::Carrot => self.carrot_reserve,
            Item::Tomato => self.tomato_reserve,
            Item::Strawberry => self.strawberry_reserve,
            Item::Melon => self.melon_reserve,
            Item::Egg => self.egg_reserve,
            Item::Milk => self.milk_reserve,
            Item::Wool => self.wool_reserve,
            Item::Fertilizer => self.fertilizer_reserve,
            _ => 0,
        }
    }

    fn min_price(&self, item: Item) -> f64 {
        match item {
            Item::Wheat => self.min_wheat_price,
            Item::Carrot => self.min_carrot_price,
            Item::Tomato => self.min_tomato_price,
            Item::Strawberry => self.min_strawberry_price,
            Item::Melon => self.min_melon_price,
            Item::Egg => self.min_egg_price,
            Item::Milk => self.min_milk_price,
            Item::Wool => self.min_wool_price,
            Item::Fertilizer => self.min_fertilizer_price,
            _ => 0.0,
        }
    }

    /// Project only unit operations that change the shed before market orders.
    /// Unit actions execute farmer-first, then live hands, before the market.
    fn projected_shed(&self, game: &Game<'_>, seat: usize, source: &Action) -> [i64; ITEM_COUNT] {
        let farm = &game.farms[seat];
        let mut shed = farm.shed;
        let mut total = farm.shed_total;
        let actions = std::iter::once(source.farmer).chain(source.hands.iter().copied());
        for (unit, action) in farm.units.iter().zip(actions) {
            let adjacent = ACCESS.contains(&unit.pos);
            if !adjacent {
                continue;
            }
            match action {
                UnitAction::Pickup(item, n) if n > 0 => {
                    let take = n.min(shed[item.index()]);
                    shed[item.index()] -= take;
                    total -= take;
                }
                UnitAction::Place(item, n) if n > 0 => {
                    let tile = &farm.tiles
                        [usize::from(unit.pos[1]) * BOARD_SIZE + usize::from(unit.pos[0])];
                    if item.is_animal()
                        && matches!(tile, Tile::Structure(s) if *s == item.animal().structure)
                    {
                        continue;
                    }
                    let take = n
                        .min(unit.inventory.amounts[item.index()])
                        .min((game.config.shed_capacity - total).max(0));
                    shed[item.index()] += take;
                    total += take;
                }
                UnitAction::Drop => {
                    for &item in &unit.inventory.order[..unit.inventory.len] {
                        let take = unit.inventory.amounts[item.index()]
                            .min((game.config.shed_capacity - total).max(0));
                        shed[item.index()] += take;
                        total += take;
                    }
                }
                _ => {}
            }
        }
        shed
    }

    pub(crate) fn apply(&self, game: &Game<'_>, seat: usize, source: &Action) -> Action {
        let mut action = source.clone();
        let day = (game.turn / game.config.turns_per_day) as i64;
        if !self.enabled || day < self.start_day {
            return action;
        }
        let fraction = if day >= self.endgame_day {
            self.endgame_sell_fraction_bp
        } else {
            self.sell_fraction_bp
        } as u64;
        let farm = &game.farms[seat];
        let projected_shed = self.projected_shed(game, seat, source);
        let mut sale_budget: [u64; ITEM_COUNT] = std::array::from_fn(|i| {
            let item = crate::data::ITEMS[i];
            let available = (projected_shed[i] - self.reserve(item)).max(0) as u64;
            available.saturating_mul(fraction) / 10_000
        });
        for order in &mut action.market {
            match order.kind {
                OrderKind::Sell(item) => {
                    let reserve = self.reserve(item);
                    let min_price = self.min_price(item);
                    if fraction == 10_000 && reserve == 0 && min_price == 0.0 {
                        continue;
                    }
                    let quote =
                        game.config.curves[item.index()].price(game.market_inventory[item.index()]);
                    if quote < min_price {
                        order.remaining = 0;
                    } else {
                        order.remaining = order.remaining.min(sale_budget[item.index()]);
                        sale_budget[item.index()] -= order.remaining;
                    }
                }
                OrderKind::Hire
                | OrderKind::BuyLand
                | OrderKind::BuyProduct(_)
                | OrderKind::BuySeed(_)
                | OrderKind::BuyAnimal(_) => {
                    if day >= self.buy_stop_day || farm.money <= self.cash_reserve {
                        order.remaining = 0;
                    }
                }
                OrderKind::Noop => {}
            }
        }
        action
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{tape::Tape, Config};
    use serde_json::json;

    #[test]
    fn rejects_unsafe_ranges_and_unknown_fields() {
        assert!(MarketOverlay::from_json(&json!({"sell_fraction_bp": 10001})).is_err());
        assert!(MarketOverlay::from_json(&json!({"surprise": 1})).is_err());
    }

    #[test]
    fn disabled_overlay_is_identity() {
        let cfg = Config::default();
        let tape = Tape::from_json(&json!([[{"market":[["SELL","WHEAT",9]]}],[{}]])).unwrap();
        let action = &tape.seats[0][0];
        let game = Game::new(&cfg, 0, [0, 0]);
        let out = MarketOverlay::default().apply(&game, 0, action);
        assert_eq!(out.market[0].remaining, 9);
    }

    #[test]
    fn enabled_defaults_are_identity_for_buy_then_sell() {
        let cfg = Config::default();
        let tape = Tape::from_json(&json!([[
            {"market":[["BUY_PRODUCT","WHEAT",13],["SELL","WHEAT",13]]}
        ],[{}]]))
        .unwrap();
        let game = Game::new(&cfg, 0, [0, 0]);
        let profile = MarketOverlay::from_json(&json!({"enabled": true})).unwrap();
        let out = profile.apply(&game, 0, &tape.seats[0][0]);
        assert_eq!(out.market[0].remaining, 13);
        assert_eq!(out.market[1].remaining, 13);
    }

    #[test]
    fn sale_uses_live_shed_reserve_fraction_and_quote() {
        let cfg = Config::default();
        let tape = Tape::from_json(&json!([[{"market":[["SELL","WHEAT",99]]}],[{}]])).unwrap();
        let mut game = Game::new(&cfg, 0, [0, 0]);
        game.farms[0].shed[Item::Wheat.index()] = 20;
        let profile = MarketOverlay::from_json(&json!({
            "enabled": true, "wheat_reserve": 4, "sell_fraction_bp": 5000
        }))
        .unwrap();
        let out = profile.apply(&game, 0, &tape.seats[0][0]);
        assert_eq!(out.market[0].remaining, 8);
    }

    #[test]
    fn sale_fraction_is_one_budget_across_repeated_orders() {
        let cfg = Config::default();
        let tape = Tape::from_json(&json!([[
            {"market":[["SELL","WHEAT",9],["SELL","WHEAT",9]]}
        ],[{}]]))
        .unwrap();
        let mut game = Game::new(&cfg, 0, [0, 0]);
        game.farms[0].shed[Item::Wheat.index()] = 20;
        game.farms[0].shed_total = 20;
        let profile = MarketOverlay::from_json(&json!({
            "enabled": true, "sell_fraction_bp": 5000
        }))
        .unwrap();
        let out = profile.apply(&game, 0, &tape.seats[0][0]);
        assert_eq!(out.market[0].remaining, 9);
        assert_eq!(out.market[1].remaining, 1);
    }

    #[test]
    fn same_turn_drop_is_saleable_before_market() {
        let cfg = Config::default();
        let tape = Tape::from_json(&json!([[
            {"farmer":["DROP"],"market":[["SELL","WHEAT",99]]}
        ],[{}]]))
        .unwrap();
        let mut game = Game::new(&cfg, 0, [0, 0]);
        game.farms[0].units[0].inventory.add(Item::Wheat, 6);
        let profile = MarketOverlay::from_json(&json!({
            "enabled": true, "min_wheat_price": 1
        }))
        .unwrap();
        let out = profile.apply(&game, 0, &tape.seats[0][0]);
        assert_eq!(out.market[0].remaining, 6);
        game.step([&out, &tape.seats[1][0]], false);
        assert_eq!(game.farms[0].shed[Item::Wheat.index()], 0);
        assert!(game.farms[0].money > cfg.starting_money);
    }

    #[test]
    fn buy_stop_preserves_slots_as_zero_remaining_orders() {
        let cfg = Config::default();
        let tape =
            Tape::from_json(&json!([[{"market":[["HIRE"],["BUY_SEED","WHEAT",9]]}],[{}]])).unwrap();
        let mut game = Game::new(&cfg, 0, [0, 0]);
        game.turn = cfg.turns_per_day * 27;
        let profile = MarketOverlay::from_json(&json!({
            "enabled": true, "buy_stop_day": 27
        }))
        .unwrap();
        let out = profile.apply(&game, 0, &tape.seats[0][0]);
        assert_eq!(out.market[0].remaining, 0);
        assert_eq!(out.market[1].remaining, 0);
    }
}

```

## Python market overlay reference

### Source: `kaggriculture_meta_lab/kaggriculture_lab/market_overlay.py`

```py
"""Python reference for the bounded Rust market overlay.

The function is intentionally pure: callers provide the live day, cash, shed,
and current sell quotes. This makes Python/Rust parity vectors straightforward.
"""
from __future__ import annotations

import copy
import math
from typing import Any

PRODUCTS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
            "EGG", "MILK", "WOOL", "FERTILIZER")
BUY_OPS = {"HIRE", "BUY_LAND", "BUY_PRODUCT", "BUY_SEED", "BUY_ANIMAL"}
ANIMALS = {"GOOSE", "COW", "SHEEP"}
ACCESS = {(4, 4), (5, 4), (4, 5), (5, 5)}

DEFAULT_PROFILE: dict[str, Any] = {
    "enabled": False, "start_day": 0, "buy_stop_day": 30,
    "endgame_day": 27, "cash_reserve": 0.0,
    "sell_fraction_bp": 10_000, "endgame_sell_fraction_bp": 10_000,
    **{f"{p.lower()}_reserve": 0 for p in PRODUCTS},
    **{f"min_{p.lower()}_price": 0.0 for p in PRODUCTS},
}


def validate_profile(raw: dict[str, Any]) -> dict[str, Any]:
    unknown = set(raw) - set(DEFAULT_PROFILE)
    if unknown:
        raise ValueError(f"unknown overlay keys: {sorted(unknown)}")
    p = DEFAULT_PROFILE | raw
    for key in ("start_day", "buy_stop_day", "endgame_day"):
        if not isinstance(p[key], int) or isinstance(p[key], bool) or p[key] < 0:
            raise ValueError(f"{key} must be a non-negative integer")
    for key in ("sell_fraction_bp", "endgame_sell_fraction_bp"):
        if not isinstance(p[key], int) or isinstance(p[key], bool) or not 0 <= p[key] <= 10_000:
            raise ValueError(f"{key} must be an integer in 0..10000")
    for product in PRODUCTS:
        key = f"{product.lower()}_reserve"
        if not isinstance(p[key], int) or isinstance(p[key], bool) or p[key] < 0:
            raise ValueError(f"{key} must be a non-negative integer")
    for key in ("cash_reserve", *(f"min_{p.lower()}_price" for p in PRODUCTS)):
        if isinstance(p[key], bool) or not isinstance(p[key], (int, float)):
            raise ValueError(f"{key} must be numeric")
        p[key] = float(p[key])
        if not math.isfinite(p[key]) or p[key] < 0:
            raise ValueError(f"{key} must be finite and non-negative")
    if not isinstance(p["enabled"], bool):
        raise ValueError("enabled must be boolean")
    return p


def project_premarket_shed(action: dict[str, Any], state: dict[str, Any]) -> dict[str, int]:
    """Project DROP/PLACE/PICKUP operations executed before this turn's market."""
    shed = {str(k): int(v) for k, v in state["shed"].items()}
    capacity = int(state.get("shed_capacity", 10**18))
    total = sum(shed.values())
    actions = [action.get("farmer", ["PASS"]), *action.get("hands", [])]
    for unit, operation in zip(state.get("units", []), actions):
        if tuple(unit.get("pos", ())) not in ACCESS or not isinstance(operation, list) or not operation:
            continue
        inventory = unit.get("inventory", {})
        op = operation[0]
        if op == "PICKUP" and len(operation) >= 3:
            item, amount = operation[1], max(0, int(operation[2]))
            take = min(amount, shed.get(item, 0))
            shed[item] = shed.get(item, 0) - take
            total -= take
        elif op == "PLACE" and len(operation) >= 3:
            item, amount = operation[1], max(0, int(operation[2]))
            if item in ANIMALS and unit.get("on_matching_animal_structure", False):
                continue
            take = min(amount, int(inventory.get(item, 0)), max(0, capacity - total))
            shed[item] = shed.get(item, 0) + take
            total += take
        elif op == "DROP":
            # Python mappings preserve the engine's insertion order.
            for item, raw_amount in inventory.items():
                take = min(int(raw_amount), max(0, capacity - total))
                shed[item] = shed.get(item, 0) + take
                total += take
    return shed


def apply_market_overlay(action: dict[str, Any], state: dict[str, Any],
                         profile: dict[str, Any]) -> dict[str, Any]:
    """Return a copied action with exactly the Rust overlay's market edits."""
    p = validate_profile(profile)
    out = copy.deepcopy(action)
    day = int(state["day"])
    if not p["enabled"] or day < p["start_day"]:
        return out
    fraction = p["endgame_sell_fraction_bp"] if day >= p["endgame_day"] else p["sell_fraction_bp"]
    shed, prices = project_premarket_shed(action, state), state["prices"]
    money = float(state["money"])
    sale_budget = {
        product: max(0, int(shed.get(product, 0)) - p[f"{product.lower()}_reserve"])
        * fraction // 10_000
        for product in PRODUCTS
    }
    for order in out.get("market", []):
        if not isinstance(order, list) or not order:
            continue
        op = order[0]
        if op == "SELL" and len(order) >= 3 and order[1] in PRODUCTS:
            product = order[1]
            reserve = p[f"{product.lower()}_reserve"]
            min_price = p[f"min_{product.lower()}_price"]
            if fraction == 10_000 and reserve == 0 and min_price == 0.0:
                continue
            if float(prices[product]) < min_price:
                order[2] = 0
            else:
                order[2] = min(max(0, int(order[2])), sale_budget[product])
                sale_budget[product] -= order[2]
        elif op in BUY_OPS and (day >= p["buy_stop_day"] or money <= p["cash_reserve"]):
            if op in {"HIRE", "BUY_LAND"}:
                order[:] = []
            elif len(order) >= 3:
                order[2] = 0
    return out

```

## R1 planner primitives

### Source: `kaggriculture_meta_lab/kaggriculture_lab/reactive_planner.py`

```py
"""R1 bounded reactive planner primitives.

This module deliberately contains no simulator-specific submission wrapper yet.
It turns an observation into a small, deterministic, safe candidate-action set;
R2 will add land/building/animal planners and R3 opponent-state features.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PlannerConfig:
    cash_reserve: int = 250
    endgame_step: int = 648
    sell_price_floor: int = 1
    max_candidates: int = 12
    worker_move_limit: int = 4


@dataclass(frozen=True)
class Candidate:
    action: dict[str, Any]
    score: float
    reason: str


def _cash(obs: dict[str, Any]) -> float:
    return float(obs.get("cash", obs.get("money", 0)))


def _step(obs: dict[str, Any]) -> int:
    return int(obs.get("step", obs.get("turn", 0)))


def _products(obs: dict[str, Any]) -> dict[str, Any]:
    value = obs.get("inventory", obs.get("storage", {}))
    return value if isinstance(value, dict) else {}


def _add(out: list[Candidate], action: dict[str, Any], score: float, reason: str) -> None:
    out.append(Candidate(action, score, reason))


def generate_candidates(observation: dict[str, Any], config: PlannerConfig = PlannerConfig()) -> list[Candidate]:
    """Generate only bounded, immediately legal-looking R1 decisions.

    The simulator remains the authority on legality. This layer avoids economic
    footguns and is deterministic: identical observations produce identical
    ordering. Observation adapters can provide richer fields incrementally.
    """
    out: list[Candidate] = []
    cash, step = _cash(observation), _step(observation)
    inv = _products(observation)
    prices = observation.get("prices", {})
    if not isinstance(prices, dict):
        prices = {}

    # R1 execution priorities: finish work before opening new work.
    for action in observation.get("urgent_actions", []):
        if isinstance(action, dict):
            _add(out, action, 1000.0, "urgent observation action")

    for action in observation.get("workers", {}).get("actions", []) if isinstance(observation.get("workers"), dict) else []:
        if isinstance(action, dict):
            _add(out, action, 800.0, "worker task supplied by adapter")

    # Sell only available stock and never below the configured floor unless in
    # endgame. Quantity is left to the adapter/simulator contract.
    for product, quantity in sorted(inv.items()):
        if not isinstance(quantity, (int, float)) or quantity <= 0:
            continue
        price = float(prices.get(product, 0) or 0)
        if price >= config.sell_price_floor or step >= config.endgame_step:
            _add(out, {"type": "SELL", "product": product, "quantity": int(quantity)},
                 500.0 + price + (100.0 if step >= config.endgame_step else 0),
                 "liquidate available stock")

    # Ask the observation adapter for legal productive actions. We score them
    # by explicit economic hints, never by arbitrary dictionary ordering.
    for item in observation.get("legal_actions", []):
        if not isinstance(item, dict):
            continue
        kind = str(item.get("type", item.get("action", ""))).upper()
        if kind in {"WATER", "HARVEST", "FERTILIZE", "PLANT", "MOVE"}:
            gain = float(item.get("expected_gain", item.get("value", 0)) or 0)
            cost = float(item.get("cost", 0) or 0)
            if cash - cost >= config.cash_reserve or kind in {"WATER", "HARVEST", "MOVE"}:
                _add(out, item, 300.0 + gain - cost * 0.01, f"safe productive {kind.lower()}")

    # PASS is always available as the final safe fallback.
    _add(out, {"type": "PASS"}, 0.0, "safe fallback")
    out.sort(key=lambda c: (-c.score, str(c.action)))
    return out[: config.max_candidates]


def choose_action(observation: dict[str, Any], config: PlannerConfig = PlannerConfig()) -> dict[str, Any]:
    """Return the highest-scoring bounded action for an observation."""
    return generate_candidates(observation, config)[0].action

```

## R2-R4 mode selector

### Source: `kaggriculture_meta_lab/kaggriculture_lab/reactive_modes.py`

```py
"""Bounded R2-R4 reactive decision layers.

These layers rank safe planner modes and emit only adapter-provided legal
candidates. They do not inspect player names or emit arbitrary simulator code.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ModeDecision:
    mode: str
    score: float
    reason: str


MODES = ("PRODUCTION", "MARKET", "ANIMALS", "EXPANSION", "RECOVERY", "ENDGAME")


def _num(obs: dict[str, Any], *keys: str, default: float = 0.0) -> float:
    for key in keys:
        value = obs.get(key)
        if isinstance(value, (int, float)):
            return float(value)
    return default


def classify_public_pressure(observation: dict[str, Any]) -> dict[str, float]:
    """Infer public economic pressures only; no player identity features."""
    prices = observation.get("prices", {})
    demand = observation.get("demand", {})
    if not isinstance(prices, dict):
        prices = {}
    if not isinstance(demand, dict):
        demand = {}
    wheat = float(prices.get("WHEAT", 0) or 0)
    wheat_demand = float(demand.get("WHEAT", 0) or 0)
    return {
        "price_pressure": max(0.0, 100.0 - wheat),
        "production_pressure": max(0.0, wheat_demand - float(observation.get("wheat_stock", 0) or 0)),
        "cash_pressure": max(0.0, _num(observation, "cash", "money") - 250.0),
        "land_pressure": max(0.0, _num(observation, "occupied_cells") - _num(observation, "available_cells")),
    }


def choose_mode(observation: dict[str, Any]) -> ModeDecision:
    """Choose a safe high-level mode using public state and time only."""
    step = int(_num(observation, "step", "turn"))
    if step >= int(_num(observation, "endgame_step", default=648)):
        return ModeDecision("ENDGAME", 1000.0, "endgame liquidation window")
    pressure = classify_public_pressure(observation)
    if _num(observation, "cash", "money") < _num(observation, "cash_reserve", default=250):
        return ModeDecision("RECOVERY", 900.0, "cash below operating reserve")
    if _num(observation, "animals_needing_feed", "animals_needing_care") > 0:
        return ModeDecision("ANIMALS", 800.0, "animal maintenance is due")
    if _num(observation, "available_cells") <= 0:
        return ModeDecision("EXPANSION", 700.0, "field capacity is exhausted")
    if pressure["price_pressure"] > 50.0:
        return ModeDecision("MARKET", 600.0, "public price pressure")
    return ModeDecision("PRODUCTION", 500.0 + pressure["production_pressure"], "productive work available")


def r2_safe_candidates(observation: dict[str, Any]) -> list[dict[str, Any]]:
    """Return adapter-supplied R2 farm-system actions with preconditions."""
    mode = choose_mode(observation).mode
    actions = observation.get("legal_actions", [])
    if not isinstance(actions, list):
        return [{"type": "PASS"}]
    allowed = {
        "ANIMALS": {"FEED", "CARE", "BUY_ANIMAL", "MOVE_ANIMAL"},
        "EXPANSION": {"BUY_LAND", "BUILD_PASTURE", "BUILD_COOP"},
        "ENDGAME": {"SELL", "HARVEST", "PASS"},
    }.get(mode, {"WATER", "HARVEST", "FERTILIZE", "PLANT", "SELL", "PASS"})
    result = [a for a in actions if isinstance(a, dict) and str(a.get("type", "")).upper() in allowed]
    return result[:12] or [{"type": "PASS"}]

```

## Our G2 selected profile

```json
{
  "index": 1,
  "name": "market-validation-00001",
  "profile": {
    "enabled": true,
    "start_day": 6,
    "cash_reserve": 250,
    "min_wheat_price": 40,
    "milk_reserve": 3
  },
  "summary": {
    "games": 112,
    "wins": 25,
    "losses": 87,
    "ties": 0,
    "score_rate": 0.22321428571428573,
    "team_balanced_score": 0.26,
    "wilson_95": [
      0.15601171396569474,
      0.30877403173207785
    ],
    "mean_margin": -16549.508928571428,
    "worst_team_score": 0.0,
    "teams": 15
  },
  "curricula": {
    "top10": {
      "games": 66,
      "wins": 23,
      "losses": 43,
      "ties": 0,
      "score_rate": 0.3484848484848485,
      "team_balanced_score": 0.37333333333333335,
      "wilson_95": [
        0.2447587406192953,
        0.4688783978696565
      ],
      "mean_margin": -8061.378787878788,
      "worst_team_score": 0.0,
      "teams": 10
    }
  }
}
```

## Upstream G3 TOP15

```json
{
  "index": 1,
  "name": "market-validation-00001",
  "profile": {
    "enabled": true,
    "buy_stop_day": 29,
    "endgame_day": 27,
    "endgame_sell_fraction_bp": 10000,
    "start_day": 6,
    "cash_reserve": 200,
    "sell_fraction_bp": 10000,
    "wheat_reserve": 10,
    "fertilizer_reserve": 5,
    "milk_reserve": 1,
    "hands_per_quadrant": 3,
    "hand_buffer": 2,
    "max_quadrants": 4,
    "land_min_hands": 5,
    "cow_target": 5,
    "sheep_target": 12,
    "goose_target": 3,
    "animal_response_bp": 5000,
    "wheat_seed_target": 160,
    "carrot_seed_target": 60,
    "strawberry_seed_target": 60,
    "melon_seed_target": 12,
    "wheat_stock_target": 20,
    "fertilizer_stock_target": 6,
    "tomato_seed_target": 24
  },
  "summary": {
    "games": 112,
    "wins": 25,
    "losses": 87,
    "ties": 0,
    "score_rate": 0.22321428571428573,
    "team_balanced_score": 0.26,
    "wilson_95": [
      0.15601171396569474,
      0.30877403173207785
    ],
    "mean_margin": -18036.714285714286,
    "worst_team_score": 0.0,
    "teams": 15
  },
  "curricula": {
    "top5": {
      "games": 36,
      "wins": 14,
      "losses": 22,
      "ties": 0,
      "score_rate": 0.3888888888888889,
      "team_balanced_score": 0.38,
      "wilson_95": [
        0.24784873065371,
        0.5513554090339485
      ],
      "mean_margin": -5845.916666666667,
      "worst_team_score": 0.0,
      "teams": 5
    },
    "top10": {
      "games": 66,
      "wins": 23,
      "losses": 43,
      "ties": 0,
      "score_rate": 0.3484848484848485,
      "team_balanced_score": 0.37333333333333335,
      "wilson_95": [
        0.2447587406192953,
        0.4688783978696565
      ],
      "mean_margin": -10448.484848484848,
      "worst_team_score": 0.0,
      "teams": 10
    },
    "top15": {
      "games": 112,
      "wins": 25,
      "losses": 87,
      "ties": 0,
      "score_rate": 0.22321428571428573,
      "team_balanced_score": 0.26,
      "wilson_95": [
        0.15601171396569474,
        0.30877403173207785
      ],
      "mean_margin": -18036.714285714286,
      "worst_team_score": 0.0,
      "teams": 15
    }
  }
}
```

## Upstream G4 TOP15

```json
{
  "index": 1,
  "name": "market-validation-00001",
  "profile": {
    "enabled": true,
    "buy_stop_day": 29,
    "endgame_day": 27,
    "endgame_sell_fraction_bp": 10000,
    "start_day": 6,
    "cash_reserve": 200,
    "sell_fraction_bp": 10000,
    "wheat_reserve": 10,
    "fertilizer_reserve": 5,
    "milk_reserve": 1,
    "hands_per_quadrant": 3,
    "hand_buffer": 4,
    "max_quadrants": 4,
    "land_min_hands": 5,
    "cow_target": 11,
    "sheep_target": 12,
    "goose_target": 3,
    "animal_response_bp": 5000,
    "wheat_seed_target": 160,
    "carrot_seed_target": 60,
    "strawberry_seed_target": 60,
    "melon_seed_target": 12,
    "wheat_stock_target": 20,
    "fertilizer_stock_target": 6,
    "tomato_seed_target": 24
  },
  "summary": {
    "games": 112,
    "wins": 29,
    "losses": 83,
    "ties": 0,
    "score_rate": 0.25892857142857145,
    "team_balanced_score": 0.29333333333333333,
    "wilson_95": [
      0.1867538856997156,
      0.34709176377898954
    ],
    "mean_margin": -17075.8125,
    "worst_team_score": 0.0,
    "teams": 15
  },
  "curricula": {
    "top5": {
      "games": 36,
      "wins": 18,
      "losses": 18,
      "ties": 0,
      "score_rate": 0.5,
      "team_balanced_score": 0.48,
      "wilson_95": [
        0.34474325409626827,
        0.6552567459037317
      ],
      "mean_margin": -2856.4444444444443,
      "worst_team_score": 0.0,
      "teams": 5
    },
    "top10": {
      "games": 66,
      "wins": 27,
      "losses": 39,
      "ties": 0,
      "score_rate": 0.4090909090909091,
      "team_balanced_score": 0.42333333333333334,
      "wilson_95": [
        0.2986741800934037,
        0.5295081029999674
      ],
      "mean_margin": -8817.863636363636,
      "worst_team_score": 0.0,
      "teams": 10
    },
    "top15": {
      "games": 112,
      "wins": 29,
      "losses": 83,
      "ties": 0,
      "score_rate": 0.25892857142857145,
      "team_balanced_score": 0.29333333333333333,
      "wilson_95": [
        0.1867538856997156,
        0.34709176377898954
      ],
      "mean_margin": -17075.8125,
      "worst_team_score": 0.0,
      "teams": 15
    }
  }
}
```

## Questions for Grok

1. Is the current G4 improvement real or selection leakage/open-loop overfit?
2. How should the full observation adapter map Kaggriculture observations into a legal farmer/hands/market action?
3. What is the smallest viable reactive planner that can beat G4 rather than merely pass unit tests?
4. Which R1-R4 design decisions are wrong or underspecified?
5. How should paired-seat same-seed controls and fresh holdout be implemented to avoid false promotion?
6. Is Rust being used in the correct layer, and where is the current CPU utilization bottleneck?
7. Propose an actionable 2-3 generation roadmap with exact experiments, metrics, and kill criteria.
8. Point out bugs, semantic mismatches, unsafe assumptions, and missing tests in the included code.
