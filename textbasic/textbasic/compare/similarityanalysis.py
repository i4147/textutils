import pandas as pd
import numpy as np
import sys

import textbasic.basic.preprocessor as ppm
# import gluonnlp as nlp

__all__ = ["extract_sim", "compare_sim"]


def compare_sim(data1, data2):
    data1_morph = ppm.morpheme_analysis(data1)
    data2_morph = ppm.morpheme_analysis(data2)

    data1_morph_set = set(data1_morph)
    data2_morph_set = set(data2_morph)
    sym_diff_set = data1_morph_set ^ data2_morph_set
    sym_diff_set_len = len(sym_diff_set)

    total_len = len(data1_morph_set) + len(data2_morph_set)
    sim_p = round((1 - sym_diff_set_len / total_len) * 100)
    return sim_p


def extract_sim(data, column=None, p=60, preserve=False):
    raw_data = data.copy()

    if isinstance(data, list):
        string_list = data.copy()
        df = pd.DataFrame(string_list, columns=["string"])
    elif isinstance(data, pd.DataFrame):
        if column is None:
            print(
                "If the data is a pandas dataframe, please enter the column name for which you want to do similarity analysis"
            )
            raise ValueError("variable name column is None")
        df = data.copy()
        string_list = df[column].tolist()
    else:
        raise TypeError("Please enter 'list' or 'pandas DataFrame' type data")
    if len(df) <= 1:
        raise ValueError("Similarity analysis is not possible for data with less than 2 data")

    group_order = 0
    fin_list = []
    sim_list = []
    unsim_list = []
    idx = 0
    while True:
        if idx in fin_list:
            idx += 1
            continue

        sys.stdout.write(f"\r $$$ {idx}/{len(raw_data)} $$$")

        try:
            stan_string = string_list[idx]
            _temp_list = [[group_order, None, stan_string]]

            fin_list.append(idx)
        except IndexError:
            break
        for i, com_string in enumerate(string_list):
            if i <= idx:
                continue
            sim_p = compare_sim(stan_string, com_string)
            if sim_p >= p:
                _temp_list.append([group_order, sim_p, com_string])
                fin_list.append(i)

        if len(_temp_list) == 1:
            unsim_list += _temp_list
        else:
            sim_list += _temp_list

        group_order += 1
        idx += 1

    print()
    unsim_list = [s[2] for s in unsim_list]
    if isinstance(raw_data, list):
        column = "string"
        whole_unsim_df = unsim_list
    else:
        whole_unsim_df = pd.DataFrame(unsim_list, columns=[column])
    whole_sim_df = pd.DataFrame(sim_list, columns=[f"group_{p}", "sim_p", column])

    if preserve:
        whole_unsim_df = raw_data.copy()

    return whole_unsim_df, whole_sim_df


# def extract_sim(data, column=None, p=60, sim_len=500):
#     '''
#     입력된 문장 리스트 또는 데이터프레임에서 유사한 문장을 그룹별로 분류하여 추출하는 함수


#     '''

#     if isinstance(data, list):
#         string_list = data.copy()
#         df = pd.DataFrame(string_list, columns=['string'])
#     elif isinstance(data, pd.DataFrame):
#         if column is None:
#             print("If the data is a pandas dataframe, please enter the column name for which you want to do similarity analysis")
#             raise ValueError('variable name column is None')
#         df = data.copy()
#         string_list = df[column].tolist()
#     else:
#         raise TypeError("Please enter 'list' or 'pandas DataFrame' type data")

#     if len(df) <= 1:
#         print('Similarity analysis is not possible for data with less than 2 data')
#         return data, pd.DataFrame()

#     new_string_list = []
#     for string in string_list:
#         new_string = string[:sim_len]
#         new_string_list.append(new_string)

#     # 형태소 분석
#     whole_morph_list_list = list(map(ppm.morpheme_analysis, new_string_list))

#     # 집합화
#     whole_morph_set_list = list(map(set, whole_morph_list_list))
#     symmetrical_diff_set_ary = whole_morph_set_list[0] ^ whole_morph_set_list[1]
#     whole_morph_set_ary = np.array(whole_morph_set_list)

#     # 유사문장
#     idx = 0
#     idx_true_list = []
#     idx_false_list = []
#     sim_df_list = []
#     while True:

#         try:
#             # 기준 문장 선정
#             stan_string_set = whole_morph_set_ary[idx]
#             idx_true_list.append(True)
#             idx_false_list.append(False)
#         except IndexError:
#             break

#         # 유사도 선정 기준값 계산
#         diff_count_stan = int(len(stan_string_set)*((100-p)/100))

#         # 유사도를 검증할 문장 추출
#         temp_morph_set_ary = whole_morph_set_ary[idx+1:]
#         # 대칭차집합 구하기
#         symmetrical_diff_set_ary = temp_morph_set_ary ^ stan_string_set

#         # 대칭차집합의 형태소 갯수 구하기
#         symmetrical_diff_len_list = list(map(len, symmetrical_diff_set_ary))
#         symmetrical_diff_len_ary = np.array(symmetrical_diff_len_list)

#         # ================================================

#         # 기준 문장 위치에 True 지정
#         idx_f_list = idx_false_list.copy()
#         idx_f_list[-1] = True

#         # 유사도 선정 기준값보다 적으면 True 많으면 False
#         f_mask_list = np.where(symmetrical_diff_len_ary <= diff_count_stan, True, False).tolist()

#         # 지금까지의 유사도 검증 결과에 추가
#         f_mask_list = idx_f_list + f_mask_list

#         # 유사한 문장을 기존 df 에서 추출
#         sim_df = df[f_mask_list]

#         # 그룹 번호 리스트 생성
#         sim_idx_ary = np.full(len(sim_df), idx)

#         # 해당 유사문장 그룹에 리스트 입력
#         sim_df.insert(0, 'group', sim_idx_ary, True)

#         # 유사문장이 최소 1개 이상 있을경우 유사문장 그룹을 저장
#         if len(sim_df) > 1:
#             sim_df_list.append(sim_df)

#         # ================================================

#         # 현재 기준문장위치에 True 가 있는 list 가져오기
#         idx_t_list = idx_true_list.copy()

#         # 유사도 선정 기준값보다 많으면 True 많으면 False
#         t_mask_list = np.where(symmetrical_diff_len_ary > diff_count_stan, True, False).tolist()

#         # 현재 기준문장위치에 True 가 있는 list에 유사도 선정 결과 리스트를 추가
#         t_mask_list = idx_t_list + t_mask_list

#         # 기존 df 에서 유사하지 않은 문장(True) 만 추출
#         df = df[t_mask_list]

#         # 기존 ary 에서 유사하지 않은 문장(True) 만 추출
#         whole_morph_set_ary = whole_morph_set_ary[t_mask_list]

#         sys.stdout.write(f'\r $$$ {idx}, {len(df)} $$$')

#         idx += 1

#     if len(sim_df_list) >= 1:
#         whole_sim_df = pd.concat(sim_df_list, axis=0)
#     else:
#         whole_sim_df = pd.DataFrame()

#     return df, whole_sim_df


# def extract_sim(data, column=None, p=60, preserve=False):
#     '''
#     입력된 문장 리스트 또는 데이터프레임에서 유사한 문장을 그룹별로 분류하여 추출하는 함수
#     '''
#     # 원본 보존
#     raw_data = data.copy()

#     # 입력데이터의 형식 파악 후 dataframe 으로 변경
#     if isinstance(data, list):
#         string_list = data.copy()
#         df = pd.DataFrame(string_list, columns=['string'])
#     elif isinstance(data, pd.DataFrame):
#         if column is None:
#             print("If the data is a pandas dataframe, please enter the column name for which you want to do similarity analysis")
#             raise ValueError('variable name column is None')
#         df = data.copy()
#         string_list = df[column].tolist()
#     else:
#         raise TypeError("Please enter 'list' or 'pandas DataFrame' type data")
#     # 데이터 갯수 필터링
#     if len(df) <= 1:
#         raise ValueError('Similarity analysis is not possible for data with less than 2 data')

#     # 형태소 분석
#     whole_morph_list_list = list(map(ppm.morpheme_analysis, string_list))

#     # 집합화
#     whole_morph_set_list = list(map(set, whole_morph_list_list))
#     symmetrical_diff_set_ary = whole_morph_set_list[0] ^ whole_morph_set_list[1]
#     whole_morph_set_ary = np.array(whole_morph_set_list)

#     # 유사문장
#     group_order = 0
#     sim_df_list = []
#     unsim_df_list = []
#     while True:
#         # 기준 문장 선정
#         try:
#             stan_morph_set = whole_morph_set_ary[0]
#         except IndexError:
#             # 더이상 비교할 기준 문장이 존재하지 않을 경우
#             break

#         # 유사도를 검증할 형태소 그룹 추출
#         temp_morph_set_ary = whole_morph_set_ary[1:]
#         # 검증 그룹의 길이
#         temp_morph_set_len_ary = np.array(list(map(len, temp_morph_set_ary)))
#         # 기준 문장 + 검증 그룹의 형태소 갯수 길이의 합
#         total_morph_set_len_ary = temp_morph_set_len_ary + len(stan_morph_set)
#         # 유사도 검증을 위한 최소 차이 기준 갯수 array 생성
#         # 100 - p 를 하는 이유는 대칭차집합의 갯수(=다른 단어 갯수)를 기준으로 유사도를 검증하기때문에
#         # 유사하지 않은 비율(100-p)를 계산해야하기 때문임
#         unsim_count_ary = np.round(total_morph_set_len_ary * (100-p) / 100)

#         # ================================================
#         # 각 형태소 그룹과 비교한 대칭차집합 구하기
#         # 대칭차집합 = 서로에게만 있는 원소집합 = 대칭차집합이 클(길)수록 유사한 형태소가 적다는 의미
#         symmetrical_diff_set_ary = temp_morph_set_ary ^ stan_morph_set
#         # 대칭차집합의 형태소 갯수 구하기
#         symmetrical_diff_len_ary = np.array(list(map(len, symmetrical_diff_set_ary)))

#         # ================================================
#         # 반복 문장 추출
#         # 최소 차이 기준 갯수보다 적은 경우는 유사문장(True), 아닌경우는 유사하지 않은 문장(False)으로 분류
#         # 첫 문장은 기준문장이므로 항상 True
#         sim_mask_list = [True] + (symmetrical_diff_len_ary <= unsim_count_ary).tolist()

#         # 이번 idx 순서 문장+유사한문장 으로 구성된 유사df 를 추출
#         sim_df = df[sim_mask_list]

#         # 그룹 번호 리스트 생성
#         sim_group_ary = np.full(len(sim_df), group_order)

#         # 해당 유사문장 그룹에 리스트 입력
#         sim_df.insert(0, f'group_{p}', sim_group_ary, True)

#         # 유사 문장이 존재할 경우 유사그룹에, 아닌경우 비유사 그룹에 저장
#         if len(sim_df) > 1:
#             sim_df_list.append(sim_df)
#         else:
#             unsim_df_list.append(sim_df)

#         # ================================================
#         # 기준문장+유사문장 을 제외한 나머지 문장 추출
#         unsim_mask_list = (~np.array(sim_mask_list)).tolist()
#         df = df[unsim_mask_list]
#         whole_morph_set_ary = whole_morph_set_ary[unsim_mask_list]

#         # ================================================
#         # 출력 & 그룹 번호 갱신
#         sys.stdout.write(f'\r $$$ {len(df)}/{len(raw_data)} $$$')
#         group_order += 1

#     print() # 한번 내려서 프린트시 다음 결과값이 내려갈 수 있도록

#     if len(sim_df_list) >= 1:
#         whole_sim_df = pd.concat(sim_df_list, axis=0)
#     else:
#         whole_sim_df = pd.DataFrame()

#     if len(unsim_df_list) >= 1:
#         whole_unsim_df = pd.concat(unsim_df_list, axis=0)
#     else:
#         whole_unsim_df = pd.DataFrame()

#     # 원본 입력이 list 형식인 경우 list 로 반환
#     if isinstance(raw_data, list):
#         if len(whole_unsim_df) >= 1:
#             whole_unsim_df = whole_unsim_df['string'].tolist()
#         else:
#             whole_unsim_df = []

#     # 원본 보존시
#     if preserve:
#         whole_unsim_df = raw_data.copy()

#     return whole_unsim_df, whole_sim_df
