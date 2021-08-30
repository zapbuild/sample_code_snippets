import { useNavigation, useIsFocused } from '@react-navigation/core';
import React from 'react';
import { View, StyleSheet, FlatList, Text } from 'react-native';
import { Container } from '../Container';
import { StackNavigationProp } from '@react-navigation/stack';
import {
  AuthParamList,
  BottomTabParamsList,
} from '../../models/navigation-params';
import { moderateScale } from 'react-native-size-matters';
import DocumentHeaderComp from '../reuse/DocumentHeaderComp';
import ListItemComp from '../reuse/ListItemsComp';
import { NoteModel, SetModel } from '../../models/models';
import { getRandomColors } from '../../utils/Common';
import { observeLatestSets } from '../../db/actions/set-action';
import withObservables from '@nozbe/with-observables';
import Config from '../../utils/Config';
import { CompositeNavigationProp } from '@react-navigation/native';
import { BottomTabNavigationProp } from '@react-navigation/bottom-tabs';
import { observeLatestNotes } from '../../db/actions/note-action';
import { observeLatestDocuments } from '../../db/actions/document-action';
import { ImageModel, RecentItems } from '../../models/models';
import ImageScannerComp from "../reuse/ImageScannerComp"

// Component props type
interface Props {
  sets: SetModel[];
  documents: ImageModel[];
  notes: NoteModel[];
}

/**
 * @returns App HomeScreen that includes latest Sets, Image documents and Notes
 */
const HomeScreen = ({ documents, sets, notes }: Props) => {
  // Navigation Type
  type NavigationProp = CompositeNavigationProp<
    StackNavigationProp<AuthParamList, 'TabScreens'>,
    BottomTabNavigationProp<BottomTabParamsList, 'Home'>
  >;
  const navigation = useNavigation<NavigationProp>();

  //View All Sets
  const onViewAllSets = () => {
    navigation.navigate('Sets');
  };

  //View All Docs
  const onViewAllDocs = () => {
    navigation.navigate("Images");
  };

  //View All Notes
  const onViewAllNotes = () => {
    navigation.navigate('Notes');
  };

  // Navigate to Test Result Screen on Set click if already has percentage
  const onSetPress = (item: SetModel) => {
    if (item.percentage != undefined && item.percentage > 0)
      return navigation.navigate("TestResultScreen", {
        setId: item.id,
      })
    navigation.navigate('ViewSetScreen', {
      setId: item.id,
      setTitle: item.title,
    });
  }

  // Navigate to ShowScannedDoc Screen on Document click 
  const onDocumentPress = (item: ImageModel) => {
    navigation.navigate("ShowScannedDocScreen", {
      image: item.document_uri
    })
  }

  // Navigate to NotesDetail Screen on Document click 
  const onNotesPress = (item: RecentItems) => {
    navigation.navigate('NotesDetail', {
      title: item?.title,
      id: item.id
    });

  };
  return (
    <Container
      headerTitle="Welcome!"
      isHomeScreen
    >
      <View style={styles.container}>
        {/**Latest Sets */}
        <DocumentHeaderComp
          title="Recent Sets"
          iconName="RecentActivityIcon"
          viewAll={sets.length >= 1 && true}
          onPress={onViewAllSets}
        />
        <FlatList
          data={sets}
          extraData={sets}
          horizontal
          showsHorizontalScrollIndicator={false}
          keyExtractor={(item) =>
            item.id ? item.id.toString() : item.title
          }
          renderItem={({ item }) =>
            <ListItemComp
              title={item.title}
              onPress={() => onSetPress(item)}
              iconName="BookWhiteIcon"
              backgroundColors={getRandomColors()}
            />
          }
        />
        {sets.length == 0 && (
          <Text style={styles.emptyText}>No Sets Yet</Text>
        )}

        {/**Latest Images */}
        <DocumentHeaderComp
          title="Recent Images"
          iconName="ImageActiveIcon"
          viewAll={documents.length >= 1 && true}
          onPress={onViewAllDocs}
        />
        <FlatList
          data={documents}
          extraData={documents}
          horizontal
          showsHorizontalScrollIndicator={false}
          keyExtractor={(item) => item.id.toString()}
          renderItem={({ item }) => <ImageScannerComp
            onPress={() => onDocumentPress(item)}
            uri={item.document_uri}
          />} />
        {documents.length == 0 &&
          <Text style={styles.emptyText}>
            No Images Yet
          </Text>}

        {/**Latest Notes */}
        <DocumentHeaderComp
          title="Recent Notes"
          iconName="RecentNotesIcon"
          viewAll={notes.length >= 1 && true}
          onPress={onViewAllNotes}
        />
        {notes.length == 0 && (
          <Text style={styles.emptyText}>No Notes Yet</Text>
        )}
        <FlatList
          data={notes}
          extraData={notes}
          horizontal
          showsHorizontalScrollIndicator={false}
          keyExtractor={(item,) => item.id.toString()}
          renderItem={({ item }) => <ListItemComp
            title={item.title}
            iconName="NotesWhiteIcon"
            backgroundColors={getRandomColors()}
            iconSize={90}
            onPress={() => onNotesPress(item)}
          />}
        />
      </View>
    </Container>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: moderateScale(15),
    paddingVertical: moderateScale(10),
  },
  emptyText: {
    alignSelf: 'center',
    fontFamily: Config.fonts.REGULAR,
    color: Config.colors.GRAY,
    paddingVertical: moderateScale(15),
  },
});

const enhance = withObservables([], () => ({
  sets: observeLatestSets(),
  documents: observeLatestDocuments(),
  notes: observeLatestNotes()
}));
// @ts-ignore
export default enhance(HomeScreen);

