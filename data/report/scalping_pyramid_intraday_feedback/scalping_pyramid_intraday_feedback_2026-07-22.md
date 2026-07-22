# 2026-07-22 Scalping Pyramid Intraday Feedback

- generated_at: 2026-07-22T09:05:02+09:00
- decision_authority: source_only_pyramid_intraday_feedback_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: intraday_threshold_mutation, intraday_runtime_apply, hard_safety_relaxation, broker_guard_bypass, order_guard_relaxation, stale_quote_bypass, cooldown_bypass, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, real_execution_quality_approval

## Summary

- pyramid_feedback_row_count: 1
- closed_pyramid_row_count: 1
- pyramid_would_have_helped_count: 0
- pyramid_correctly_blocked_count: 0
- pyramid_overheat_or_reversal_risk_count: 1
- pyramid_open_unresolved_count: 0
- one_share_event_count: 72
- one_share_closed_count: 3
- one_share_pyramid_opportunity_count: 1
- one_share_pyramid_missed_upside_count: 1
- one_share_pyramid_missed_upside_rate: 0.33
- one_share_pyramid_avg_opportunity_cost_pct: 0.78

## Blocker Metrics

- blocker=profit_not_enough sample=1 recovered_rate=0.00 reversal_rate=1.00 blocked_then_recovered_rate=0.00

## Rows

- record_id=20932 code=064820 name=케이프 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=0.63 final=0.63 ai=77.0 tick=1.25 micro_vwap=27.91

## One Share Opportunity Rows

- record_id=21838 code=270660 name=에브리봇 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21841 code=090360 name=로보스타 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21847 code=102940 name=코오롱생명과학 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=1.4 opportunity_cost=1.4 final=0.0
- record_id=21837 code=058610 name=에스피지 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21839 code=466100 name=클로봇 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21846 code=448900 name=한국피아이엠 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21844 code=089890 name=코세스 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21854 code=004000 name=롯데정밀화학 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21858 code=102940 name=코오롱생명과학 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21849 code=000250 name=삼천당제약 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21850 code=002020 name=코오롱 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21848 code=460930 name=현대힘스 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=1.49 opportunity_cost=1.49 final=1.1
- record_id=21863 code=000990 name=DB하이텍 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21851 code=117730 name=티로보틱스 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21862 code=082740 name=한화엔진 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21860 code=484810 name=티엑스알로보틱스 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21867 code=084370 name=유진테크 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21870 code=124500 name=아이티센글로벌 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21875 code=126340 name=비나텍 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21872 code=009420 name=한올바이오파마 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21871 code=039030 name=이오테크닉스 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21876 code=278280 name=천보 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21843 code=000500 name=가온전선 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21868 code=042700 name=한미반도체 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21882 code=006110 name=삼아알미늄 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21878 code=008060 name=대덕 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21885 code=460930 name=현대힘스 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21884 code=131290 name=티에스이 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21845 code=459510 name=나우로보틱스 label=pyramid_would_have_helped opportunity_seen=True opportunity_profit=1.66 max_profit=2.44 opportunity_cost=0.78 final=2.35
- record_id=21877 code=314930 name=바이오다인 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21893 code=394280 name=오픈엣지테크놀로지 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21892 code=397030 name=에이프릴바이오 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21869 code=488900 name=비츠로넥스텍 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21891 code=388210 name=씨엠티엑스 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21890 code=082920 name=비츠로셀 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21887 code=046890 name=서울반도체 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21894 code=459510 name=나우로보틱스 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21899 code=000120 name=CJ대한통운 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21896 code=437730 name=삼현 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21895 code=338220 name=뷰노 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21906 code=200710 name=에이디테크놀로지 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21905 code=352820 name=하이브 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21904 code=475400 name=씨메스로보틱스 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21910 code=199430 name=케이엔알시스템 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21911 code=388720 name=유일로보틱스 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21903 code=455900 name=엔젤로보틱스 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21897 code=049070 name=인탑스 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21888 code=012330 name=현대모비스 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21909 code=473980 name=노머스 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21842 code=108490 name=로보티즈 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21886 code=307950 name=현대오토에버 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21919 code=453340 name=현대그린푸드 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21916 code=079900 name=전진건설로봇 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21917 code=281820 name=케이씨텍 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21918 code=010060 name=OCI홀딩스 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21840 code=277810 name=레인보우로보틱스 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21861 code=222800 name=심텍 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21925 code=002240 name=고려제강 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21921 code=005070 name=코스모신소재 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21928 code=356860 name=티엘비 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21873 code=022100 name=포스코DX label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21938 code=483650 name=달바글로벌 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21934 code=077970 name=STX엔진 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21929 code=271940 name=일진하이솔루스 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21933 code=486990 name=노타 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21935 code=323280 name=태성 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21930 code=006400 name=삼성SDI label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21924 code=017670 name=SK텔레콤 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21936 code=011210 name=현대위아 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21989 code=015760 name=한국전력 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21993 code=389650 name=넥스트바이오메디컬 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=21987 code=007660 name=이수페타시스 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
