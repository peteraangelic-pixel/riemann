_K='consecutive_unwatered'
_J='watered_today'
_I='planted_day'
_H='player'
_G='yield_units'
_F='kind'
_E='step'
_D=None
_C=True
_B='PASS'
_A='hands'
import base64,bz2,copy,json
from typing import Any
ACTIONS=json.loads(bz2.decompress(base64.b85decode('LRx4!F+o`-Q&|*gwd(<3y`O*(1b^^9@87zoOB@PdPagQ76aWMe000000000000000000000000000000000001St?zB!Ex=3aS7A0YNALQ2+n|KmY(D0w4uM015yA2tcYuN-7mqB~nlVs1TrtprnNaAS6Jb01y}e8Z^)bO#z_D4FdoJMw$T0pfni)pkM%K(?A(C27@3p3;+!pXagpI&}0UHQc^_FniEEmrc-EYX^c>LJy0s1qDexPL5Kjv000N^e3KW}{8c!g@aW9L49wzAWF$z*F{ZL(TA4Yd&SaUabB=O3nXOG^&T~lT9CB+Kk|e~*i1V1{GBMa$#g&*?%(Aj%jFFyAYD7sUM8>jALS&id5^6OQS*;q8GA5^(6HRL|G9-+WOk{?<9E9XGsi~U7lamq?juJyz4Acza%$%Ikb2MaYh>S=i5@19KOcF7PJeo{NB21Gr8sw1^D=@|}gDhEQWc-iC_&RYuX0x1$ANDmll5^%wYE1d^a~>w9ypvqlo@viK*1641Y5Y9SOiYA)jYvuJ=Nx(ewK>F(G?V8)Co)IojZJGr`SY3iJf2LBan64n^YhQ)`SNGT<Z?ur<Z4XuCclnrUNnz2^UZub)}nq*N9WEt@u-=pBU)#W^O>Vwa&wx~Q&LVwqmLYNNinW#Txkb0T9K}6Nb#qS;T}FT(isynCJ!~uamZp!YBdr*eDhvTJo8+VK22+0O>%k1o_RdxwI_~qnt2mk)|{G}pE=BA^UUPtanq0f1gGqN<g8T;ixo>LMj}{+U*#kp5g1iWlPV-(Llr7vCMZbCn5qn_n1C4}ULLG^zp0G4ILybunw<aM=bkmM`csq1$s@_leCB-ANv}1jInOmDo@vRNB-G^Nlg>1rO-^ey@jOpCrzD4(^IY;|YHP$!X*sS#n$+`&%|^J_5a%_CB>$oF@;v<f{MR|=PJVNfl0JM%u4_@r&N<}rNhjoaK78YvkDv53*CSI+X*`+EYmvz3CXzoq*Cu&CHK&O2A3WEeK5Lr!^Itq^^UgW*=REUSu5136=aPBmPmjaRaXIpN=bm$(H8bR7jdRU-@Z@r4rm|0ylZ|s(^PKa~>zwoPIXSP7pP!lLLm~58Yg0{WJ|t^e)YmyR<kaLzKQ*m6$2qS&YhG$kBT3JnIWjfolg7MrNe_~9M-$|l)^U?s`R2JZ=gib{O=fFaYvYn~aWvGN^G}oK&-3Rwsh&SI&phXzMw~=`Mw29yB+2C0@y$Hey!><WNHbp}<H@g@n&VuW=DtmM^IDqMJet<0^q)M|weig-#=PdauRQ0P)|$xIH7A}=5v@*n$eiKgYmReXdCp{yKRn~iYv#P<h~r*)Cb>DuG}kr6`5N<@<Ho$xS?4@?=OpLPn%6bsUp3Droc}e*_}9&Ii6qv)Ij(bG=bAYm#<k9C<o=Ty{y#abYv<?3Gv>9;eCIUR9(lu>)@#Z5=Q*zubDYgd$e*0^&nGn>`x<MS*P702kDg~dk*_()q?so*H8m&k&T=Na*Avg2_?(_;@=Z@U&m5YQQgd3@ns|O`^YiD&KR#xnf0NEnHTlmur-=OH$m8a<#Cgt7oaY`yHLYrXbMu-{nrm90n*2v6o;26bn)$7B&*PqR`kax?Yw~lSHODedY4ObXoSq|E^NlB()bf5!bH=phoaVpd&P4vdK0nXn=N}sUh?(U4=CfSmnE8{EPGtWhU!H53BjnW7$)syh&NUPB$;~;h$*(-*<MW@K@-_Zz=gmGfq>^XOeCM3})@z*SK0KP#^PX}~8rHcp@^R<QI7cE*ajt9R@@vnYdFRibO?-S#MCTll%;(RX_;~r_&phYGxRQMHN6$0PIO2J&a(|rCb6Sl|^Yh1^X`1tsoR2)zKQ%Pgr=L9MHK{fJO@3=yl73EnlQpl-a(U*prynMyNj#k4u5+2rX*KhcT#=gO=frvQpB(ZgeCC|zHK^vN&1=s!Bv0x&`OZ9_J~<yX=C!HKHOS{bCo)Gg^G;~jB-XjjNRwQdsmzln&1!R>9&;nkM!eRwK6&RqkIobG%}!(F=QYi1nrSmh<6P#m&ph%q=QGZECUeQoXp>XUYCMiVHN>8C=g8sn<5GFApEaKu8q|q7^Uh?{nKiF9lUno6bIyF6^OH^|k@L^bJoz3^&o#+1d98EKIg`id&1;@W@_gp9K5IG6WRgkb*PPdnlU_b*YIC18&OGNMTE`}*HL2uz%{8XArkd8L$*yUq`T5Ty@jfKv^Nn&zCXqF*9!94owWx`$Je*JK&1yL$&zjfIn&i?P)cn^cnrm8~bA;x#HLgSW&l=a7bI&=?#MjBGB#}Jl9(d;yUp4%5^Usb<`K=_5Yg*G&PsDMqHRh(iIj56PpAt3m$2qM{e42^Gn)s8+<B>dh=DGZN@$>WJ<niXD(ma}zUz3t*a!HLzImp*JH8rQ0!!wDdpOGh#9Gslz^{sKHn)6zm`9C@2eDjVZM4HK|rkZ@`IjQEFNu1N?K5LoJ<IYIqUp2<H^ImIQd6P{~IOh^1#+v-+JaTiB&3xA!n$2mc;yzC^UOdR0@f^vmX{r5Ab6S#TBSel(YtD0-ubkGJXyP&=HK`h!(^}J9)~7Z3=A6kR$>+~LPd<6CoaZ&?&TEZpS*bPo&PkF&XU{dwBT+I)kk`-6c#?e6Up{=~=kcva9}`obn)8VX`TT3nMx=@6q<(Xbf5$n_O-@O#;u@UiH77qOIplNCHL05Ck;(Zq^XE0G$@9sl^)>Q*<eHk1^YdJD^Nn*f|23%R$<2Qp;(4ue_~Xd(YGl;c9Mtnpd7ft^=O(^SB1E2f&T>eJsm*EgQ^voE^PeIla%1N+U*y!B*PMSGYDkeetknKI)^bGhY4T|KA0$qE%{7^>e;#sqB-D>J$vHJVoSt~(c^*GCsU9S0sWV#gIUh4g8u`zY&1!4JNzOQ$=A73#IXSLJB-H-7!bqId{L}dS)5pol$Z01zsWhBV;(5(Yc+{Ny^P2PiHS^D(Go07;=Z<P?=RP>`=QSiwd8eK~iTUTrsrlik%}+V0tu+%9Q!`Uq)+EG(Qfp34LPY$W=DeEx*0Oo$GI{4QCQqJnPBog;CbiF=b6VGtt$!YP^UTrY&2gzbkCRjKbNtqRerc&De4708&of?6Ba@ouy!`WDKaY)g$ucHq$*BB|O+shqpFU5M=QXW3ob%^AdGlIxG&Q0pIj(b(Yvk5R&p6U@YG)*z#+sVc^PlI>9GLkUnIk5+n&!2xbCXjan$k%bGx6s%j!aCPk{U#rk_kR}rxQHaiTzJGuao-x&V15&Blv4v)cohqGsKxWCbj3ya%YZd$dj7XiOy?}k;vw?tmpB~aj!W(dF1Ek9DLLK<LBp^n)Bn&K1t1UjY&B<CUQiY*0rXZNcl5boaUOD<mWl9PalqaM?QS>ljP^doZ@TenrddG=f^Ws&1uh*S)-Fv=8-iLMEut$Jmj2l$mHac&-nf^&yghgC+4|4jd>=28uQJ66H}i)bI0bj5@hpQlZo>=o=N0u$)={7nrl)?HLTP=InGTroP5_OJUPUftVEeL8q-aGTGnKflTjr3u5(gqKjZk<n$(ldO-@dHdCne4pU0e<^W=H2HRqqiesLahYhRrF@@x9zpPqhxd~$PBTIAQ0%;ssXPn^`|o_zC@QO<nkxu&9g^OMbarlz%|^Hb*ydFS=>=aKpIpPq7jnddc)CZw3uO>0tfoRc~6CbL|e<mWPH8csE+Owu%*YhN|2l6;zZK2Aw8eAknj)S5~1Ij(Eu^IX?8r!}Hy&U4Qs$kft4Nv&!%#-wXaYo8P6pFT<FG@m@@o@qJpIi73C;pErxt$F#*PtQC~5i|2%Cq5%u)@n7cj!DRxb53T7uQ{)tWcl-x$MN~CPdWIU`K=;($(rZmoYZSM%-1~g$mDshYg(FlJdQ~kYg&n|M10n~=bt9NeB^xBIjw0t=gvI;KQxg)&3XBx{N}%}GhFg(pPK%%d8Fj=%+%MK)cHPq*N~Cq&P<$|nIlt3kBHYenrm8|(rf3BIP+dlC!RxykmQnPlUkEa9yQ6#(rf0vPD$pqu1-IQ*Ufz7X{1LdB<6l=Q}~{9JbxPUO!Ln?^T?l?<a1ibpVyp^AD=a;<6oY9`ORzOktU(fk3M|UUTabF{Q1s)erd-eQ_VQ%oYax|$2I1(oaa3AU&PIRd7?gRU!Oit<IIziPnvU1az1mM)00o0Y3DiQ=QW-@*0kjOk3MPh=Dd=8(kGnP`RAN`_>+^3c{Jnm=g*!=GEbc6CnuV6G?}T*W}hdXM~z1{%_Cfqtu&uG&Uq&|^G<oKYt2ngN#~i*CbaXMl1*}akCE{nMEN3fO@ExvB%EtfHQ}hA)Xhx%)~C;p;m;yTBhQ-r`SYGN`5ffek<LzY&nGpGdF1DfbI%%TX{M%e97!XbPEXE%9%sawpB&bwk<Dv}Oq_^@vzp|Djz+buK7MKQ<6k~=ne)z0H6+bBtw)-8=CtP;Pm!sfesRt<=N$R@K6w9$@^j?Vn*8VIk0<A!IW%f#<ox_=QLi<UXET~>n%B=Y@*YV4Jo)p-=BA&T`8hn+q?tU{rV@T@=j8FkYgsw+YtK3TYl+V@T%X6B^U1Drob#NVPdUVrYI1Qo=bY5?a${3YdHFfdA3WEZjX6KboaSmo&Uw$zn#muNG@qR2zJ7f3=gj>4Y3Io@Y9^YEYo9#vGs&8d$>$z8nK?BlG@mujO*PLs<df#LCP;jr$Il<1J~_>2km4ut^O?-nnvQw>b3Z>ceoT@-<MUjfCZzc@H6O#A=1Gajn&e5zJZoH<Pd;(T@;sW2Ygw))nnPUHam`~>lls@3YhE=utzv$2IV7BE$<888W~7=-l0U6^G02e9O(c`Z|35tQCbaQ5(oQv|vrR~xiKdaM{c*`8awbN+pVWBrNRmdst~vfp|Bv|BoR7{(iKevF%|y~`&L{QH=`&N}Yg$S1HRRTFUUQt&TG1!@&1CahpPxC*)M`lAn&%qUq9(b`CpDgPQ#my<YfU0GHLYu0)}x6MHR5xck;v9gL~3hKlTv3jsi=}`S*E0!sm*Fh%+|H78j?nzoaCNOXNdfbb3}=$r#Z>VtxwHzIg)B?=D6m*YvZ1IJoC;@L&?s0&2g?I*Ajf5bI&~a^XK{JKQd}+LQgrzCk|>NYDw}r&1+Lx=QW&?b6keGn$Ad*T9c8<B%hN$eDOJ{8b`#O<VcuFIU0!}CY*PAJG;A`&W|9!*d;xHl=}pd{J@mSAk?S}=&C9B756W=KL$SbIvi$a4=|@08I_q#$$kt@%$+egF^v$3i6`c>P?6+ZWo9hPGcz({D$KJhF<FI~V-qr_am99J$&z6Si6%)BU^%9V26OXVjL8`w$udkyl1UJmB*&9eBw-|GdIF&P(wF#CAF7xYf6%DDvL$~3Nj^lWG8t4axk!i2RWho2BBA}#m-$qV3aRSJKQ&R|RV(=!B^@HaHBs*)-juz^>dZ)yG9pNcn2^MiGZh%gW?7kqnOTg?NRmvEk}^VMNtl^MS&K6)S%Wh&nU-XkiI}q@%w{ZN#z;w-k|dFm5ebnYCPXB}jFFKrNs|?KB}wpA3%IJD0*mieKSWA)RN|z*Kz3B~BERb-OqhuzNs=Z>n36JNiIXNtB21AYLPklGB#{#&$%v3hi82!;$&zH4lL<0Ji3yTOnI<I3lO%|V5Sb*BCNgBn2#GNhB*cj_BP2|ikrE`4B#0szWX!8EGbUza#u<c}Adr~^nKDF4G9o02B#9CdB4$Z4L`2ClOvXteB$7!oBxHn`M97&UCL~Om5hNs%BuK<bA|#SYF_8%*1Wd`2Oh}U?BuJAaM3E+9Nis<!BxIPA5@KYMGE9>p5t1??6C{#Ek|GHtW=WD}NW_UVB*=u4BuR*g8Imz3WRemj%t?rhh)77u5eYLSlM)gn$s!XbNr?#=B$$aZL`j(@NQfk2Oon9{nT9gVF_o5NgouQhB1o8$OvWoRv4&Y>%Q6{^Oi6-95-^a&m`F1vW=k@!(N#Psk@~*IVG?9QL`Z~*ks?flWJ!`Fl1!3Fgh-f>l0=y#gh-h(NrFNX7?6nxgo%+NM1+|W5=oL|$cd6BOp;<rB1}n%5eX9}LL|hJF)<`aM8uhyCS-z186=r9Ns?rVCMHBkgh-5&5QNDI5)wp`NQovyl44|xh=`ITnIy=BOo=9BnG+IXNfRWJL}ZwWnIa^ai6mr%$tGlyV<JeA5=6-nCPXA8#zZk7h?69eM3WN{F(ibUGDL(V%!o{hGA2lwA|yzXK_Mnggp878l424uA|yzRk`W?gNf3mRWF(RjA|@nBBuNqyNfDAHNJx<ol0-~o%w}1WCQCA~#hHkVNJ)Z8l1#}FB1njmLlOxxOw7q7W=Ro<hDgaWNQ6vCNg_rhB*`R_Ns%EDCP|SA5?NuHmS#-MV)qn7<RdYRm6$UrGb1o&21sOy5i%n(CL|VRm@LX!iZcP3nVBD2M}(zQq9t}!3*4!}Q2DAy^ho)U<f2EwOXjE4Djy|5KE+7N`%@xVvZDJ+Ua3psU{&!Wu&S9*Pnx8=im8C&p8+R8cuR_+tO~x>QPE4#RZjqXid=S4*`CUxtRv)A2V|d8q<fX*OvW<IV$95DGd)El_o0NU%A<-TUs9@jBJyEbk9jOX#th0=5-TX;7?T8&B*`;1h|Dz-%$1o;#$wE~4h8U4A0a)2b`jxKJyk_nM2-<FrBwD5lhsuB3JmbfV;?d|i3FLFM3PL2l42qWk}_l@nI=e?B4mjsNg_;1ButYcBxIS1lM+cJl1NF35s-+HBPK>f%#e|hBqW59B4S}96CoocnIt4glQKk1kuoGml1Va5ks~C?k|aqIWXUokB#9v+Oi2<XnIj@Z$pj>jjFKivCP|qlOo=i{FqsJui5Vo5B#eoelM-Y|nGqz(B4TDp$udZZGDL|IB4mt_B$$y9$r5CYl0=yj5s@-UktCTUlMx{#nUX}2B4o@-CP^YpnI=ghF(yfo2$>R0nF%CJnIcTYB#{t=kc^UIM3O>D7?UJPAtofVEX-k<W(=&EV$6vV5@JarL}E;nB*~DFlOY6&GZI9RB4mk@CPYF>iIXBmNRc8$l42rAM42K<2_%V;2@+u>$(ba`krN^^Mj~X0l4QvlGE9*mk&zJ+CP5}7$uScdB$7!H5=_Z5B!rnFB#|VEnGq6XNhFCfWJ!`FOqi1-$&ivHOp_$UnTVMQB$*;akdq`#$e1LA$udkxl1!3JlQSg5l42%A%#$%Bi6oJPl4O}Al1P$FBuO$NNhT6RNhV2|36UfuL?mKNkR-xP$t28@B1sZL1d>T4gou#|GDb{9jF5<tktEELWX4GnOh}R@M9C5)5=_Yv6C}wYB4mj(DVfDo;vV%+dZtQXtSLC2Y|KourI|}ItYk)5%twM|NoG`%W(16r86zZWGf>F{Oi3nWj7XC)5hDo+1dPpVOlGDTshJ}&6B#C^8jQxKY6${NB*qdF5+r7(H87DNlQJSn1Vb`LMAo!O!a&s2#zbaDVywjD6~-22CS@6nWtgnW#z@9liJ6%dnJmjNxWwZu%Mt{PBnc8^n9NBsGa7?a2{4Gs5+o5Yk&+T-Ns<XOB+SVKj3h|OGC?CG!bVA&n9S6Ol0=x)$*m+Nw9Q6pW@=&~CSpW`Q!^TY5RoC02{jp*)FjMElO$$ICP-v~BP0z*2{2~0tTiG@m`K*OCS@}e%w`P0nTpJ@6A3Yr0z{G|OpL<JS(7p|D>E@OD9p1iGI5hKGbNa_6wF3sm{AXBqb61}GbEEF$e4*DWW<C?5+Y=hB*`LVl1P$Fl0+nvB*>W(5)x)fGGZn~A|gzQ851NVkrGLeNhFyvNXSA=h)6_8lMxa~kupgWBuSDa$t02{B#|*BnGz(EB#|K^A|gUU5RzoVCP;`$nK2}Z5+X?^LP*GwCP<MYNeM9`NhU;?h)9zpkuow#5@Jk|C5B5ejF`!oW-BtxB*`))jFFKNCP^_SA~7V0i7_S-2_(r9NFqp*At5G2$&y5oB4#9!5fCO!lO&TQ#E6k1L=qAr5+p>4nKEQa6B104A|^?a36motNhC<fgqV^NVkD6hCP@hrM94^zW+Fr+#DqkWB!tXJk%^K?5g{@}$uc5Hi83U~AqgZT$cd9ONfJq!B20p0i6Uf4B!q;?Fp(t4h{*{eB*=*}B21BzWQdt2WQ3ALl0hb6CS=IT2$D#VCM1(0WSJ2pnUYL|i6mr6B$1Ltl0hWN2$DubnIw*ZUP7vRs*jl;;Zi;*dKE#^knlvVB=;#0^;JwNr0G>XRENbxkK+AU{_JK2hFO_2EF&bwNXaCaNs=)lL`<29HH>7?k&;Y;Ohm|#lOjn3f=o$-OpzuMW+FrhFp@?{$r&Re5;92{i6q355(xy6B+N|9EHf;^aTSY+k|JVENRuKklQKz|%%)|TW=z8}Wt50XktE285i=1oMkFE$Bt*!VkdkIoGP4<#m}4x)U^6nwnNs5_<1QgFafW4PEM&~fA(l$a%wr@HB$EjwNsP>r7|P6*mQu`S8HJgQh-8T}LL`KlgqX=0As~`Oi8Ca^WtgKf%(EGk%qC=*(Ts+Z6C{w4B#@Db5@eW?MkEn2CKDu?i4rnN2{DltGcjf}3o&L^WoA|+B*cs)$V8aPkj%=QRgN-D$jq$7%v?&b#ztjkDVY{yGO>(gvkb+U%*>-QnUtA{nJmUKW)@|T$&g7QB$*>5A{CZqGYc_hBxWqjB$y&3M8ZUpWQfLQF;vW?%nZt7G7@GQ%rUJbB*cu7hGkijW-}u*F<FtBA%v1LNic{>B#|UyM3_iPm?Xg?Fk>pr8I>~=GFfG21({|n#h9|nV-!d-Ovw^R%##usBQaT!#w^Orti_ol5F}(t7?FgD2^KPt;s+c?VzVsB%w|}{nV3w<##xnSBobsyW<-!kNh1<6B#AL5W=RnVGD|E>#hA>dVzVq_B1j}=WQ2(fks?VXL`V{5L?nqaWQiD%k&<H~NhV0lBq0)GBuHjvkkn>sWY)C}MoEbn)Y54*jTsEoB*>CUi4rq4kkTYcCQUSIYfVjNlOr{fCTcYqtdm;JWNJt?4M^6aYE5e-A|%FSYc-jvjA}8%D~wiT%o8w+CNl{#VnRfjCJ`iJCNjoY!x>n`jI3lN5hTG8CPYb*A`%Ehi6$mUNsVEdtwKg(LnO?Q#Ds<<GE9>hB1T9OVoc1L5@JatBpD+zBMAhUNJM5x$t006mStvHnPSX~F_|+JnPw(sm_vbCae<j;S(L_ODrQQ|D>A8=Ga$wc#h8|1n30JRB$Fh;CSpLwDVYq)W@aX3Ga_Y@%*=(DW<xTAFk>N@OvGkZVOC)?CNi0ZWm%M|!6zI{%FH7%W-}&bEQFX6W@JGoNhCy>B#e=nAW4`=kt9r#Ok_z3BqYR{lM^u+iI^FP%%zxFjKeWAD>7M?m_}rogE1MFWXz$MjF`zW5J`ebF(Hx`V#a1OB}WxeU)vxKy6`XN%0JT}{8<-FrF6t*SM+3;7#%V{t17x;x@3Ng72SmCmv%{Ui0;7hXG}QCza|G5h1r!(?3p1m=9-9pYdJWF{l*XYg22SaW@N=<5X_}!D=^Hes^YHacLyJnk1}SnTI9_}JpQ@!5BQw(&;F^eKjY7z$Dh>v{MM$Xr##d?erY^06T6NmoMi`QQl92QSDP<3LB<`K9Ac|524b!;MaCx?6lM#I>Ez<7re#yjlgX7lI&pSn&z@^DkddGLjMUE@YG$YTFD5%O8Pks@Q0auPCRI$t7n>ln!-73nN2?0%%BwO<F<fL<8Fyl4GY57N(+k5SF6^Edp>)MFDvu@*%(J^Vti^s!NeMiRH4`Sa&So{OW@dgs!LQ;!K7WorX|E!G!}$EuUymQ>kLqXR`23TP^ZfZW{~zZ*d`$D7pOK8uA^#H$aw_s<dN5B$RoR)9D>AQECwG&8%#nJqk0wFt%2SM$c4ZlbCw5nc7o!S}n2s`3?!>FZDo2wAafzKcRO2b=$(akL7n3PwW(DDtbi=227iL81iagkznRsOjv6SNh$K=$SkI2EqGEbUoGdVK>|HJ<7hCGLpUp1OZ7{to(#~2+k2N_<Br0I~Sc0?XMp3Hb-*`CaLG3IgT>EXr3db^p&4w&|MXH54TdOcirO#IY;A0M7heEBu}f1l@{C(VDy{C<4#^IxAne_nj^Psy*%asGMye;=QZ$o@Q^o_v||PdPRIe;oe5jePzlzD;NRe@#D${v`RY;(y1S=1KXjO+Pu#erc(i|2+SXHT`SziSy5&)B65Dj!)~)_@6w~{=R-^8FcC7^mOp^czAeraow4no^GD6XS~TVB$<dwGD$HeL^4Q(m`Rx-2uUJBMoA__Vq_#qiIEdBB$!DiNhTzal1Pk_B1FhUkrHH*BP1lr43i{8!bCzznHe%jl1#*zB21GcNQB7|B#DwF$r4E<kt8BwNSO%{l4O~PnKDF3k&;A`LPkl6GD$K?7>Ooin37D%86hJi$cd6hNs>g#GE7L2h>(&<m`RdIMogI#B$Fh`1eqixh{=)(CQtOI@_oXpaN-!MzhFv#uu6X5l==cwfRy?IQ{V)r><LT>ObJii5}!ayU?o0)l;9;k@g;m&O0S3|Km1+E6yZWZQKr|d')))
def _base(observation):A=observation;B=int(A.get(_H,0));E=min(int(A.get(_E,0)),719);C=copy.deepcopy(ACTIONS[B][E]);D=A.get('farms')or[];F=D[B].get(_A)or[]if B<len(D)else[];C[_A]=(C.get(_A)or[])[:len(F)];return C
HARVEST_AGE={'WHEAT':3,'CARROT':3,'MELON':10,'STRAWBERRY':10,'TOMATO':8}
ACCESS={(4,4),(5,4),(4,5),(5,5)}
EVENING_WATER_HOUR=17
ENDGAME_DAY=28
RECOVER_URGENT=_C
RECOVER_ENDGAME=_C
RECOVER_ANIMALS=_C
RECOVER_DROP=_C
def _walk(pos,target):
	A,B=pos;C,D=target
	if A<C:return['EAST']
	if A>C:return['WEST']
	if B<D:return['SOUTH']
	if B>D:return['NORTH']
	return[_B]
def _near(cells,pos,claimed):
	A=claimed;B=[B for B in cells if B not in A]
	if not B:return
	C=min(B,key=lambda c:(abs(c[0]-pos[0])+abs(c[1]-pos[1]),c[1],c[0]));A.add(C);return C
def _local_safe_action(tile,inventory,day,hour):
	C='HARVEST';B=day;A=tile
	if not isinstance(A,dict):return
	if A.get(_F)=='WEED':return['DIG']if RECOVER_URGENT else _D
	if A.get(_F)=='PLANT':
		D=A.get('crop');E=B-int(A.get(_I,B));F=E>=HARVEST_AGE.get(D,999)and int(A.get(_G,0)or 0)>0;G=not A.get(_J);H=int(A.get(_K,0)or 0)>=1
		if RECOVER_ENDGAME and F and B>=ENDGAME_DAY:return[C]
		if RECOVER_URGENT and G and(H or hour>=EVENING_WATER_HOUR):return['WATER']
		return
	I=A.get('animal')
	if I and RECOVER_ANIMALS:
		if int(A.get(_G,0)or 0)>0:return[C]
		if not A.get('fed_today')and int(inventory.get('WHEAT',0)or 0)>0:return['FEED']
		if not A.get('cared_today'):return['CARE']
		if A.get('fertilizer_available'):return['COLLECT_FERTILIZER']
def recover(observation,base_action):
	X='market';O='farmer';G=base_action;C=observation;P=int(C.get(_H,0)or 0);Q=C.get('farms')or[]
	if P>=len(Q):return G
	L=Q[P];H=L.get('tiles')or[]
	if not H:return G
	I=int(C.get('day',int(C.get(_E,0)or 0)//24)or 0);Y=int(C.get('hour',int(C.get(_E,0)or 0)%24)or 0);Z=C.get('private')or{};M=Z.get('inventories')or[];N=[L.get(O,[4,4]),*(L.get(_A)or[])];A=[list(G.get(O)or[_B])];A.extend(list(A)for A in G.get(_A)or[]);A=A[:len(N)];A.extend([[_B]]*(len(N)-len(A)));R=[];S=[]
	for(D,a)in enumerate(H):
		for(F,E)in enumerate(a):
			if not isinstance(E,dict)or E.get(_F)!='PLANT':continue
			if not E.get(_J)and int(E.get(_K,0)or 0)>=1:R.append((F,D))
			b=E.get('crop');c=I-int(E.get(_I,I))
			if I>=ENDGAME_DAY and c>=HARVEST_AGE.get(b,999)and int(E.get(_G,0)or 0)>0:S.append((F,D))
	T=set()
	for(B,K)in enumerate(N):
		if not isinstance(K,(list,tuple))or len(K)<2:continue
		J=int(K[0]),int(K[1]);F,D=J
		if D<0 or D>=len(H)or F<0 or F>=len(H[D]):continue
		U=M[B]if B<len(M)and isinstance(M[B],dict)else{}
		if not A[B]or A[B][0]!=_B:continue
		V=_local_safe_action(H[D][F],U,I,Y)
		if V is not _D:A[B]=V;T.add(J);continue
		d=(S if RECOVER_ENDGAME else[])if I>=ENDGAME_DAY else R if RECOVER_URGENT else[];W=_near(d,J,T)
		if W is not _D:A[B]=_walk(J,W)
		elif RECOVER_DROP and J in ACCESS and sum(int(A or 0)for A in U.values())>=90:A[B]=['DROP']
	return{O:A[0]if A else[_B],_A:A[1:],X:list(G.get(X)or[])}
def agent(observation,configuration=_D):A=observation;return recover(A,_base(A))
act=agent