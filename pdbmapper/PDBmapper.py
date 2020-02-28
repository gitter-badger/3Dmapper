# coding: utf-8

# Import necesary modules
import sys
import os
import re
import glob
import pandas as pd
import numpy as np
from .db_parser import parser
# .interface_parser import reshape
from .decorator import tags
from .explode import explode
from .logger import get_logger
from ncls import NCLS


def PDBmapper(protid,  geneid, transcritpID, psdb, vardb, out_dir, pident, isoform, consequence, varid=None):
    '''
    Map interfaces and genomic anntoated variants and returns a
    setID.File, necessary input for SKAT. Additionaly, it creates
    another file with detailed information regarding the maped areas.

    Parameters
    ----------
    protid : str
        Ensembl protein ID
    geneid : str
        Translated Ensembl protein ID
    psdb : str
        Directory where to find interface database
    vardb : str
        Directory where to find variants database
    out_dir : str
        Output directory
    pident : int
        Thershold of sequence identity (percertage).

    Returns
    -------
    setID.File
        txt file containing a data frame two columns corresponding to the
        analyzed interface id and the corresponding annotated genomic variants.
    MappedVariants.File
        Same as setID.File but with additional information describing the
        interfaces and the variants.
    '''
    # log file
    logger = get_logger(' PDBmapper', out_dir)

    # parse interfaces corresponding to the selected protein ID
    psdf = parser(protid, psdb)

    if psdf.empty:
        logger.error('Interfaces of protein ' +
                     protid + 'could not be parsed.')
        raise IOError
    else:
        logger.info('Interfaces of protein ' + protid + ' parsed.')

    # if database is compacted and explode is needed

    columns_type = psdf.applymap(lambda x: isinstance(x, list)).all()
    columns_list = columns_type.index[columns_type].tolist()

    # cols_stack
    cols_stack = psdf.apply(lambda x: x.astype(
        str).str.match(r'[a-zA-Z0.-9]+-[a-zA-Z0.-9]+'))
    colsnames_stack = psdf.columns[cols_stack.any()].tolist()

    if any(cols_stack) is True:
        for col in colsnames_stack:

            psdf.loc[:, col] = psdf[col].str.replace(
                '-', ',')
            psdf.loc[:, col] = psdf[col].str.split(',')

        psdf = explode(
            psdf, colsnames_stack)

    elif columns_list is not None:
        psdf = explode(
            psdf, columns_list)
    else:
        psdf[colsnames_stack] = \
            psdf[colsnames_stack].astype(str)

    # if default database is used minor modifications are needed
    if pident is not None:
        logger.info('Filtering interfaces by pident = ' + str(pident) + '%.')
        # filter by pident
        pident = int(pident)  # from str to int
        psdf_pident = psdf.loc[psdf.Pident >= pident]
        # if pident threshold is to high, the next maximum value of pident is
        # notified in log file
        if psdf_pident.empty:
            alt_pident = psdf.loc[:, "Pident"].max()
            logger.error('Warning: for protid ' + str(pident) +
                         ', the variable "Pident" equal to ' +
                         str(pident) + ' is too high.\n A threshold lower than or equal to ' +
                         str(alt_pident) + ' would retrieve results.')

            raise IOError()

    # parse variants corresponding to the selected protein ID
    annovars = parser(geneid, vardb)
    logger.info('Variants file from gene id ' + geneid + ' parsed.')

    # filter by transcript ID
    annovars = annovars[annovars['Feature'] == transcritpID]
    if annovars.empty:
        raise IOError()

    # filter by variant type if one or more selected
    if consequence is not None:
        annovars = annovars[annovars['Consequence'].astype(
            str).str.contains('|'.join(consequence))]
        logger.info('Filter of features = ' + str(consequence))

        # if filter returns an empty df, raise error
        if annovars.empty is True:
            logger.error(
                'Variants could not be filtered by feature type = ' + consequence)
            raise IOError()

    # filter by variant type if one or more selected
    if varid is not None:
        if 'Existing_variation' in annovars.columns:
            annovars = annovars[
                annovars['Uploaded_variation'].astype(
                    str).str.contains(varid) |
                annovars['Existing_variation'].astype(
                    str).str.contains(varid)]
        else:
            annovars = annovars[
                annovars['Uploaded_variation'].astype(
                    str).str.contains(varid)]
        logger.info('Variant \'' + str(varid) + '\' has been selected.')
        # if filter returns an empty df, raise error
        if annovars.empty:
            logger.error(
                'Variants could not be filtered by variant id \'' + str(varid) + '\'')
            raise IOError()

    # for variants with high impact affecting several aminoacidic positions,
    # the protein position is a range. split the range to have each position
    # individually
    if any(annovars['Protein_position'].astype(str).str.contains(r'[0-9]-[0-9]')):
        # subset hight impact variants
        sub_df = annovars[annovars['Protein_position'].astype(str).str.contains(
            r'[0-9]-[0-9]')]
        # subset the remaining variants to concatenate afterwards
        remaining_df = annovars.drop(sub_df.index)
        # split the range or interval
        sub_df[['start', 'end']] = sub_df['Protein_position'].str.split(
            '-', expand=True)
        # sometimes the start or the end position of the interval is a
        # question mark. In that case, we take into account the
        # remaining value of the interval
        if any(sub_df['start'].str.contains('\?')):
            sub_df['start'] = np.where(sub_df['start'] == '?', sub_df['end'],
                                       sub_df['start'])
        if any(sub_df['end'].str.contains('\?')):
            sub_df['end'] = np.where(sub_df['end'] == '?', sub_df['start'],
                                     sub_df['end'])
        # create the range of numbers defined by the interval
        sub_df['Protein_position'] = sub_df.apply(lambda x: list(
            range(int(x['start']), int(x['end'])+1)), 1)
        # spread each individual position into one row
        sub_df = explode(sub_df, ['Protein_position'])
        # drop unnecesary columns
        sub_df.drop(['start', 'end'], inplace=True, axis=1)
        # concatenate final result
        annovars = pd.concat([remaining_df, sub_df], sort=False)

    # for sucessful merge, Protein_position column must be str type
    psdf['Protein_position'] = psdf['Protein_position'].astype(str)
    annovars['Protein_position'] = annovars['Protein_position'].astype(str)
    # Merge them both files
    mapped_variants = annovars.join(
        psdf.set_index('Protein_position'), on='Protein_position', how='inner')
    # Merge them both files
    location_variants = annovars.join(
        psdf.set_index('Protein_position'), on='Protein_position', how='outer')

    v = psdf.loc[:, 'Protein_start_position':'Protein_end_position'].apply(
        tuple, 1).tolist()

    # you can also use `from_arrays`
    idx = pd.IntervalIndex.from_tuples(v, closed='both')
    # print(annovars.Protein_position.values)
    # print(psdf.set_index(idx))
    # print(idx.get_loc(annovars.Protein_position.values.astype(int).tolist()))
    # print(idx.get_indexer(2045))
    print(psdf.Protein_start_position.values)
    ncls = NCLS(psdf.Protein_start_position.values,
                psdf.Protein_end_position.values,
                psdf.Protein_start_position.values)
    it = ncls.find_overlap(2045)
    print(it)
    # muts = list(
    #    map(int, annovars.Protein_position.values))
    # print(muts)
    # print(idx.get_loc(annovars.Protein_position.values))
    # l = idx.get_indexer(
    #    annovars.Protein_position.values[0:1].astype(int).tolist())

    # print(l)
    # stop if there are no results
    if mapped_variants.empty:
        # report results
        logger.warning('Warning: ' + protid +
                       ' does not map with any annotated variant.\n')
        raise IOError()

    # if merging was successful, create setID file and
    # save the merged dataframe as well
    else:
        setID_file = mapped_variants[['Structure_feature_id',
                                      'Uploaded_variation']]
        setID_file.drop_duplicates(inplace=True)
        mapped_variants.drop_duplicates(inplace=True)

        # Save the merged dataframe, appending results and not
        #  reapeting headers
        with open(os.path.join(out_dir, ('setID_pident' + str(pident) + '.File')), 'a') as f:
            setID_file.to_csv(f, sep=',', index=False,
                              header=f.tell() == 0)
        with open(os.path.join(out_dir, ('MappedVariants_pident' + str(pident) + '_isoform_' +
                                         '_'.join(isoform) + '_consequence_' + '_'.join(consequence) + '.File')), 'a') as f:
            mapped_variants.to_csv(f, sep=',', index=False,
                                   header=f.tell() == 0)

    del(psdf, psdf_pident, annovars)
